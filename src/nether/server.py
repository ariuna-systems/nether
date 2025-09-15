import argparse
import asyncio
import logging
import traceback
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from aiohttp import hdrs as headers
from aiohttp import web, web_urldispatcher
from aiohttp_middlewares import cors

from .modules import Module
from .exception import ServiceError
from .logging import configure_logger
from .message import Command, Event, FailureEvent, Message, SuccessEvent

local_logger = logging.getLogger(__name__)
local_logger.propagate = False
configure_logger(local_logger)


@dataclass(frozen=True, kw_only=True, slots=True)
class StartServer(Command):
    host: str
    port: int

    def __post_init__(self) -> None:
        if self.port <= 0:
            raise ValueError("port must be positive number")
        # TODO validate host


@dataclass(frozen=True, kw_only=True, slots=True)
class ServerStarted(SuccessEvent): ...


@dataclass(frozen=True, kw_only=True, slots=True)
class StartServerFailure(FailureEvent): ...


@dataclass(frozen=True, kw_only=True, slots=True)
class StopServer(Command): ...


@dataclass(frozen=True, kw_only=True, slots=True)
class ServerStopped(SuccessEvent): ...


@dataclass(frozen=True, kw_only=True, slots=True)
class StopServerFailure(FailureEvent): ...


@dataclass(frozen=True, kw_only=True, slots=True)
class RegisterView(Command):
    route: str
    view: type[web.View]


@dataclass(frozen=True, kw_only=True, slots=True)
class ViewRegistered(SuccessEvent): ...


@dataclass(frozen=True, kw_only=True, slots=True)
class RegisterViewFailure(FailureEvent): ...


@dataclass(frozen=True, kw_only=True, slots=True)
class AddStatic(Command):
    prefix: str
    path: Path
    kwargs: dict[str, Any] = field(default_factory=lambda: {})


@dataclass(frozen=True, kw_only=True, slots=True)
class StaticAdded(SuccessEvent): ...


@dataclass(frozen=True, kw_only=True, slots=True)
class AddStaticFailure(FailureEvent): ...


type ServerSignals = (
    StartServer
    | ServerStarted
    | StartServerFailure
    | StopServer
    | ServerStopped
    | StopServerFailure
    | RegisterView
    | ViewRegistered
    | RegisterViewFailure
    | AddStatic
    | StaticAdded
    | AddStaticFailure
)


class HTTPInterfaceServiceError(ServiceError): ...


class _DynamicRouter:
    def __init__(self, app: web.Application, logger: logging.Logger = local_logger):
        self._http_server = app
        self.logger = logger
        self._resource_map: dict[str, list[web_urldispatcher.AbstractResource]] = {}

    def add_view(self, route: str, view_class: type[web.View]) -> None:
        resource = self._create_resource(route)
        self._add_resource(resource)
        resource.add_route(headers.METH_ANY, view_class)

    def add_route(
        self,
        method: str,
        path: str,
        handler: web_urldispatcher.Handler | type[web.View],
        *,
        name: str | None = None,
        **kwargs,
    ) -> None:
        resource = self._create_resource(path, name=name)
        self._add_resource(resource)
        resource.add_route(method, handler)

    def add_static(
        self,
        prefix: str,
        path: Path,
        *,
        name: str | None = None,
        expect_handler: web_urldispatcher._ExpectHandler | None = None,
        chunk_size: int = 256 * 1024,
        show_index: bool = False,
        follow_symlinks: bool = False,
        append_version: bool = False,
    ) -> None:
        if prefix.endswith("/"):
            prefix = prefix[:-1]
        resource = web_urldispatcher.StaticResource(
            prefix=prefix,
            directory=path,
            name=name,
            expect_handler=expect_handler,
            chunk_size=chunk_size,
            show_index=show_index,
            follow_symlinks=follow_symlinks,
            append_version=append_version,
        )
        self._add_resource(resource)

    def _add_resource(self, resource: web_urldispatcher.AbstractResource) -> None:
        key = self._resource_key(resource)
        self._resource_map.setdefault(key, []).append(resource)

    def _create_resource(self, path: str, *, name: str | None = None) -> web_urldispatcher.Resource:
        if path and not path.startswith("/"):
            raise ValueError("Path must start with `/` or be empty.")

        if self._is_plain_path(path):
            return web_urldispatcher.PlainResource(path, name=name)
        return web_urldispatcher.DynamicResource(path, name=name)

    @staticmethod
    def _is_plain_path(path: str) -> bool:
        has_template = "{" in path or "}" in path
        has_argument_fields = web_urldispatcher.ROUTE_RE.search(path)
        return not has_template and not has_argument_fields

    @staticmethod
    def _resource_key(resource: web_urldispatcher.AbstractResource) -> str:
        canonical = resource.canonical
        if "{" in canonical:
            before_dynamic = canonical.partition("{")[0]
            part_before_slash, sep, _ = before_dynamic.rpartition("/")
            index_key = part_before_slash if sep else before_dynamic
        else:
            index_key = canonical
        index_key = index_key.rstrip("/")
        return index_key if index_key else "/"

    @staticmethod
    async def _resolve_dynamic_route(
        request: web.Request, resource_index: dict[str, list[web_urldispatcher.AbstractResource]]
    ) -> tuple[web_urldispatcher.UrlMappingMatchInfo | None, set[str]]:
        allowed_methods: set[str] = set()
        match_info = None
        url_part = request.rel_url.path_safe
        while url_part:
            resources = resource_index.get(url_part)
            if resources is not None:
                for resource in reversed(resources):  # Iterate from newest
                    match_info, allowed = await resource.resolve(request)
                    if match_info is not None:
                        return match_info, allowed_methods
                    allowed_methods = allowed_methods.union(*allowed)
            if url_part == "/":
                break
            url_part = _DynamicRouter._truncate_path(url_part)
        return match_info, allowed_methods

    @staticmethod
    def _truncate_path(url_part: str) -> str:
        last_slash_index = url_part.rfind("/")
        if last_slash_index <= 0:
            return "/"
        return url_part[:last_slash_index]

    @web.middleware
    async def middleware(
        self, request: web.Request, handler: Callable[[web.Request], Awaitable[web.StreamResponse]]
    ) -> web.StreamResponse:
        route_manager: _DynamicRouter = request.app["dynamic_router"]
        resource_index = route_manager._resource_map

        # Debug logging for incoming requests
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(
                f"Processing request: {request.method} {request.path_qs} from {request.remote or 'unknown'}"
            )
            self.logger.debug(f"Available route prefixes: {list(resource_index.keys())}")

        match_info, allowed_methods = await _DynamicRouter._resolve_dynamic_route(request, resource_index)
        if match_info is None:
            if allowed_methods:
                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug(
                        f"Method {request.method} not allowed for {request.path}. "
                        f"Allowed methods: {sorted(allowed_methods)}"
                    )
                return web.Response(status=405, text="Method Not Allowed")

            # Try the default handler (for static files, etc.)
            try:
                response = await handler(request)
                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug(f"Default handler served: {request.path} -> {response.status}")
                return response
            except web.HTTPNotFound:
                # This is a 404 - log detailed information in DEBUG mode
                if self.logger.isEnabledFor(logging.DEBUG):
                    self._log_404_debug_info(request, resource_index)
                raise  # Re-raise to let aiohttp handle the 404 response
            except Exception:
                traceback_details = traceback.format_exc()
                self.logger.error(f"Internal server error for {request.method} {request.path}: {traceback_details}")
                return web.Response(status=500, text="Internal Server Error")

        try:
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"Route matched: {request.path} -> {match_info.handler}")

            match_info.add_app(request.app)
            request.__dict__["_match_info"] = match_info
            del request.__dict__["_cache"]["match_info"]  # Force re-evaluate cached match_info
            new_handler = cast(type[web.View], match_info.handler)
            if getattr(new_handler, request.method.lower(), None) is None:
                if self.logger.isEnabledFor(logging.DEBUG):
                    available_methods = [
                        m
                        for m in ["get", "post", "put", "delete", "patch", "head", "options"]
                        if hasattr(new_handler, m)
                    ]
                    self.logger.debug(
                        f"Method {request.method} not implemented by {new_handler.__name__}. "
                        f"Available methods: {available_methods}"
                    )
                return web.Response(status=405, text="Method Not Allowed")

            response = await new_handler(request)
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"View {new_handler.__name__} served: {request.path} -> {response.status}")
            return response
        except Exception:
            traceback_details = traceback.format_exc()
            self.logger.error(f"Error in view handler for {request.method} {request.path}: {traceback_details}")
            return web.Response(status=500, text="Internal Server Error")

    def _log_404_debug_info(
        self, request: web.Request, resource_index: dict[str, list[web_urldispatcher.AbstractResource]]
    ) -> None:
        """Log detailed information about 404 errors when in DEBUG mode."""
        self.logger.debug(f"404 NOT FOUND: {request.method} {request.path}")
        self.logger.debug(f"Query string: {request.query_string}")
        self.logger.debug(f"Headers: {dict(request.headers)}")

        # Log all registered routes for debugging
        if resource_index:
            self.logger.debug("Registered dynamic routes:")
            for prefix, resources in resource_index.items():
                for resource in resources:
                    if hasattr(resource, "_path"):
                        self.logger.debug(f"  {prefix} -> {resource._path}")
                    else:
                        self.logger.debug(f"  {prefix} -> {resource.canonical}")

        # Log static routes from the main router
        app_router = request.app.router
        if hasattr(app_router, "_resources"):
            static_routes = [r for r in app_router._resources if isinstance(r, web_urldispatcher.StaticResource)]
            if static_routes:
                self.logger.debug("Registered static routes:")
                for route in static_routes:
                    self.logger.debug(f"  {route._prefix} -> {route._directory}")

        # Suggest similar paths
        all_paths = set()
        for resources in resource_index.values():
            for resource in resources:
                if hasattr(resource, "_path"):
                    all_paths.add(resource._path)
                else:
                    all_paths.add(resource.canonical)

        if all_paths:
            similar_paths = [p for p in all_paths if p and any(part in request.path for part in p.split("/") if part)]
            if similar_paths:
                self.logger.debug(f"Similar registered paths: {similar_paths}")


class Server(Module[StartServer | StopServer | RegisterView]):
    def __init__(
        self,
        application,
        *,
        configuration: argparse.Namespace,
        logger: logging.Logger = local_logger,
        cors_origins: list[str] | None = None,
        aiohttp_loggers_verbosity: int = 0,
    ):
        super().__init__(application=application)
        self._http_server = web.Application()
        self._http_server["configuration"] = configuration

        # Configure logging based on configuration if log_level is available
        if hasattr(configuration, "log_level"):
            from .logging import configure_global_logging

            configure_global_logging(log_level=configuration.log_level)
            # Update logger level to match configuration
            if logger == local_logger:
                logger.setLevel(getattr(logging, configuration.log_level.upper(), logging.INFO))

        dynamic_router = _DynamicRouter(self._http_server, logger=logger)

        self._http_server["dynamic_router"] = dynamic_router
        self._http_server.middlewares.append(self.track_requests)

        if cors_origins is not None:
            self._http_server.middlewares.append(cors.cors_middleware(origins=cors_origins))
        self._http_server.middlewares.append(dynamic_router.middleware)

        self.host = configuration.host
        self.port = configuration.port

        self.logger = logger
        self.runner: web.AppRunner | None = None
        self.tasks: set[asyncio.Task[Any]] = set()
        self._is_running = False

        # Configure aiohttp loggers based on our debug level
        aiohttp_log_level = logging.DEBUG if logger.isEnabledFor(logging.DEBUG) else logging.WARNING
        for logger_name in [
            "aiohttp.access",
            "aiohttp.client",
            "aiohttp.internal",
            "aiohttp.server",
            "aiohttp.web",
            "aiohttp.websocket",
        ]:
            aiohttp_logger = logging.getLogger(logger_name)
            aiohttp_logger.handlers.clear()
            aiohttp_logger.propagate = False
            aiohttp_logger.setLevel(aiohttp_log_level)
            configure_logger(aiohttp_logger, verbose=aiohttp_loggers_verbosity)

    @web.middleware
    async def track_requests(
        self, request: web.Request, handler: Callable[[web.Request], Awaitable[web.StreamResponse]]
    ) -> web.StreamResponse:
        task = asyncio.current_task()
        if task is not None:
            self.tasks.add(task)

        # Log request details in DEBUG mode
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"Incoming request: {request.method} {request.path_qs}")
            if request.headers:
                self.logger.debug(f"Request headers: {dict(request.headers)}")

        try:
            response = await handler(request)

            # Log response details in DEBUG mode
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"Response: {response.status} for {request.method} {request.path}")

            return response
        except web.HTTPException as e:
            # Log HTTP exceptions (like 404, 405, etc.) in DEBUG mode
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"HTTP Exception: {e.status} {e.reason} for {request.method} {request.path}")
            raise
        except Exception as e:
            # Log other exceptions as errors
            self.logger.error(f"Unhandled exception in request {request.method} {request.path}: {e}")
            raise
        finally:
            if task is not None:
                self.tasks.discard(task)

    async def on_start(self) -> None:
        if self.runner is not None:
            raise HTTPInterfaceServiceError("Server is already running.")

        self.runner = web.AppRunner(self._http_server)
        await self.runner.setup()
        tcp_site = web.TCPSite(self.runner, self.host, self.port)
        await tcp_site.start()

        self.logger.info(f"Server started on {self.host}:{self.port}.")

        # Log all registered routes in DEBUG mode
        if self.logger.isEnabledFor(logging.DEBUG):
            self._log_all_routes()

        self._is_running = True

    def _log_all_routes(self) -> None:
        """Log all registered routes for debugging purposes."""
        self.logger.debug("=== Registered Routes ===")

        # Log static routes from main router
        main_router = self._http_server.router
        if hasattr(main_router, "_resources"):
            static_resources = [r for r in main_router._resources if isinstance(r, web_urldispatcher.StaticResource)]
            if static_resources:
                self.logger.debug("Static routes:")
                for resource in static_resources:
                    self.logger.debug(f"  {resource._prefix} -> {resource._directory}")

            # Log regular routes from main router
            regular_resources = [
                r for r in main_router._resources if not isinstance(r, web_urldispatcher.StaticResource)
            ]
            if regular_resources:
                self.logger.debug("Main router routes:")
                for resource in regular_resources:
                    path = getattr(resource, "_path", getattr(resource, "canonical", str(resource)))
                    self.logger.debug(f"  {path}")

        # Log dynamic routes
        dynamic_router = self._http_server.get("dynamic_router")
        if dynamic_router and hasattr(dynamic_router, "_resource_map"):
            resource_map = dynamic_router._resource_map
            if resource_map:
                self.logger.debug("Dynamic routes:")
                for prefix, resources in resource_map.items():
                    for resource in resources:
                        if isinstance(resource, web_urldispatcher.StaticResource):
                            self.logger.debug(f"  {prefix} -> {resource._directory} (static)")
                        else:
                            path = getattr(resource, "_path", getattr(resource, "canonical", str(resource)))
                            self.logger.debug(f"  {prefix} -> {path}")

        self.logger.debug("=== End Routes ===")
        self.logger.debug("If you're getting 404 errors, check if your requested path matches any of the above routes.")

    async def on_stop(self) -> None:
        if self.runner is None:
            raise HTTPInterfaceServiceError("Server is not running.")

        for site in self.runner.sites:
            await site.stop()

        if self.tasks:
            self.logger.info(f"Waiting for {len(self.tasks)} ongoing requests before shutdown.")
            try:
                await asyncio.wait_for(asyncio.gather(*self.tasks, return_exceptions=True), timeout=10.0)
            except TimeoutError:
                self.logger.warning("Shutdown timed out, active requests were killed.")

        await self.runner.shutdown()
        await self.runner.cleanup()

        self.runner = None
        self.logger.info("Server stopped.")
        self._is_running = False

    async def handle(self, message: Message, *, handler: Callable[[Message], Awaitable[None]], **_: Any) -> None:
        if not isinstance(message, self.supports):
            return

        result_event: Event | None = None
        try:
            match message:
                case RegisterView():
                    await self._add_view(route=message.route, view=message.view)
                    result_event = ViewRegistered()
                case AddStatic():
                    await self._add_static(prefix=message.prefix, path=message.path, **message.kwargs)
                    result_event = StaticAdded()
                case StartServer():
                    try:
                        await self.on_start()
                        result_event = ServerStarted()
                    except Exception as error:
                        result_event = StartServerFailure(error=error)
                case StopServer():
                    try:
                        await self.on_stop()
                        result_event = ServerStopped()
                    except Exception as error:
                        result_event = StopServerFailure(error=error)
        except Exception as error:
            match message:
                case RegisterView():
                    result_event = RegisterViewFailure(error=error)
                case AddStatic():
                    result_event = AddStaticFailure(error=error)
                case StartServer():
                    result_event = StartServerFailure(error=error)
                case StopServer():
                    result_event = StopServerFailure(error=error)
        finally:
            if result_event is not None:
                await handler(result_event)
            else:
                # fallback: unknown message type or error
                self.logger.error(f"Unhandled message type: {type(message).__name__}")

    async def _add_view(self, *, route: str, view: type[web.View]) -> None:
        """If app frozen, adds the view to the dynamic route manager; otherwise, adds it to the router."""
        if self._http_server.frozen:
            self._http_server["dynamic_router"].add_view(route, view)
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"Added dynamic view `{view.__name__}` to frozen app at route: {route}")
        else:
            self._http_server.router.add_view(route, view)
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"Added view `{view.__name__}` to router at route: {route}")
        self.logger.info(f"View `{view.__name__}` assigned to route {route}")

    async def _add_static(self, prefix: str, path: Path, **kwargs) -> None:
        if self._http_server.frozen:
            self._http_server["dynamic_router"].add_static(prefix, path, **kwargs)
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"Added dynamic static route: {prefix} -> {path} (frozen app)")
        else:
            self._http_server.router.add_static(prefix, path, **kwargs)
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"Added static route: {prefix} -> {path}")

        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info(f"Static route added: {prefix} -> {path}")
