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

from nether.common import Command, Event, FailureEvent, Message, SuccessEvent
from nether.console import configure_logger
from nether.exceptions import ServiceError
from nether.service import Service

local_logger = logging.getLogger(__name__)
local_logger.propagate = False
configure_logger(local_logger)


@dataclass(frozen=True, kw_only=True)
class StartServer(Command):
  host: str
  port: int


@dataclass(frozen=True)
class ServerStarted(SuccessEvent): ...


@dataclass(frozen=True)
class StartServerFailure(FailureEvent): ...


@dataclass(frozen=True, kw_only=True)
class StopServer(Command): ...


@dataclass(frozen=True)
class ServerStopped(SuccessEvent): ...


@dataclass(frozen=True)
class StopServerFailure(FailureEvent): ...


@dataclass(frozen=True, kw_only=True)
class AddView(Command):
  route: str
  view: type[web.View]


@dataclass(frozen=True)
class ViewAdded(SuccessEvent): ...


@dataclass(frozen=True)
class AddViewFailure(FailureEvent): ...


@dataclass(frozen=True)
class AddStatic(Command):
  prefix: str
  path: Path
  kwargs: dict[str, Any] = field(default_factory=lambda: {})


@dataclass(frozen=True)
class StaticAdded(SuccessEvent): ...


@dataclass(frozen=True)
class AddStaticFailure(FailureEvent): ...


class HTTPInterfaceServiceError(ServiceError): ...


class _DynamicRouter:
  def __init__(self, app: web.Application, logger: logging.Logger = local_logger):
    self.app = app
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

    match_info, allowed_methods = await _DynamicRouter._resolve_dynamic_route(request, resource_index)
    if match_info is None:
      if allowed_methods:
        return web.Response(status=405, text="Method Not Allowed")
      try:
        return await handler(request)
      except Exception:
        traceback_details = traceback.format_exc()
        self.logger.error(f"{traceback_details}")
        return web.Response(status=500, text="Internal Server Error")

    try:
      match_info.add_app(request.app)
      request.__dict__["_match_info"] = match_info
      del request.__dict__["_cache"]["match_info"]  # Force re-evaluate cached match_info
      new_handler = cast(type[web.View], match_info.handler)
      if getattr(new_handler, request.method.lower(), None) is None:
        return web.Response(status=405, text="Method Not Allowed")
      return await new_handler(request)
    except Exception:
      traceback_details = traceback.format_exc()
      self.logger.error(f"{traceback_details}")
      return web.Response(status=500, text="Internal Server Error")


class HTTPInterfaceService(Service[StartServer | StopServer | AddView]):
  def __init__(
    self,
    *,
    configuration: argparse.Namespace,
    logger: logging.Logger = local_logger,
    cors_origins: list[str] | None = None,
    configure_aiohttp_loggers: bool = True,
  ):
    self.app = web.Application()
    self.app["configuration"] = configuration

    dynamic_router = _DynamicRouter(self.app, logger=logger)
    self.app["dynamic_router"] = dynamic_router
    self.app.middlewares.append(self.track_requests)
    if cors_origins is not None:
      self.app.middlewares.append(cors.cors_middleware(origins=cors_origins))
    self.app.middlewares.append(dynamic_router.middleware)
    self.host = configuration.host
    self.port = configuration.port

    self.logger = logger
    self.runner: web.AppRunner | None = None
    self.tasks: set[asyncio.Task[Any]] = set()
    self._is_running = False

    # Configure aiohttp loggers
    if configure_aiohttp_loggers:
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
        configure_logger(aiohttp_logger)

  @web.middleware
  async def track_requests(
    self, request: web.Request, handler: Callable[[web.Request], Awaitable[web.StreamResponse]]
  ) -> web.StreamResponse:
    task = asyncio.current_task()
    if task:
      self.tasks.add(task)
    try:
      response = await handler(request)
      return response
    finally:
      if task:
        self.tasks.remove(task)

  async def start(self) -> None:
    host = self.host
    port = self.port

    if self.runner is not None:
      raise HTTPInterfaceServiceError("Server is already running.")

    self.runner = web.AppRunner(self.app)
    await self.runner.setup()
    tcp_site = web.TCPSite(self.runner, host, port)
    await tcp_site.start()
    self.logger.info(f"Server started on {host}:{port}.")
    self._is_running = True

  async def stop(self) -> None:
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

  async def handle(self, message: Message, *, dispatch: Callable[[Message], Awaitable[None]], **_: Any) -> None:
    if not isinstance(message, self.supports):
      return

    result_event: Event
    try:
      match message:
        case AddView():
          await self._add_view(route=message.route, view=message.view)
          result_event = ViewAdded()
        case AddStatic():
          await self._add_static(prefix=message.prefix, path=message.path, **message.kwargs)
          result_event = StaticAdded()
    except Exception as error:
      match message:
        case AddView():
          result_event = AddViewFailure(error=error)
        case AddStatic():
          result_event = AddStaticFailure(error=error)
    finally:
      await dispatch(result_event)

  async def _add_view(self, *, route: str, view: type[web.View]) -> None:
    """If app frozen, adds the view to the dynamic route manager; otherwise, adds it to the router."""
    if self.app.frozen:
      self.app["dynamic_router"].add_dynamic_view(route, view)
    else:
      self.app.router.add_view(route, view)
    self.logger.info(f"View `{view.__name__}` assigned to route {route}")

  async def _add_static(self, prefix: str, path: Path, **kwargs) -> None:
    if self.app.frozen:
      self.app["dynamic_router"].add_static(prefix, path, **kwargs)
    else:
      self.app.router.add_static(prefix, path, **kwargs)
