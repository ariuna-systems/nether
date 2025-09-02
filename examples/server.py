import asyncio
import json
import platform
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import nether
from aiohttp import web
from nether.component import Component
from nether.message import Command, Event, Message
from nether.server import RegisterView, Server


class System(nether.Nether):
    def __init__(self, configuration):
        super().__init__(configuration=configuration)
        self.start_time = time.time()

    async def main(self) -> None:
        print("Started")


class SystemStatusView(web.View):
    """Web view to display system status and information."""

    async def get(self) -> web.Response:
        """Handle GET request to show system status."""
        system: System = self.request.app["system"]
        mediator = system.mediator

        # Calculate uptime
        uptime_seconds = time.time() - system.start_time
        uptime_hours = int(uptime_seconds // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
        uptime_secs = int(uptime_seconds % 60)

        # Get component information
        components = []
        for component in mediator.components:
            component_info = {
                "name": component.__class__.__name__,
                "type": str(type(component).__module__ + "." + type(component).__name__),
                "supports": str(component.supports),
                "state": "running",  # Could be enhanced with actual state
            }
            components.append(component_info)

        status_data = {
            "system": {
                "name": "Nether System",
                "version": getattr(nether, "__version__", "unknown"),
                "uptime": f"{uptime_hours:02d}:{uptime_minutes:02d}:{uptime_secs:02d}",
                "uptime_seconds": int(uptime_seconds),
                "start_time": system.start_time,
            },
            "platform": {
                "python_version": platform.python_version(),
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "processor": platform.processor(),
            },
            "mediator": {
                "component_count": len(mediator.components),
                "context_count": len(mediator._contexts),
            },
            "components": components,
        }

        # Return JSON response
        return web.json_response(status_data, dumps=lambda obj: json.dumps(obj, indent=2))


class StatusRegistrationComponent(Component[RegisterView]):
    """Component to handle status view registration after server startup."""

    def __init__(self, application, server):
        super().__init__(application)
        self.server = server
        self.registered = False

    async def on_start(self) -> None:
        await super().on_start()
        if not self.registered:
            # Store system reference in the HTTP app for the status view
            self.server._http_server["system"] = self.application

            # Register the system status view
            async with self.application.mediator.context() as ctx:
                await ctx.process(RegisterView(route="/status", view=SystemStatusView))

            self.registered = True
            print("System status available at: http://localhost:8082/status")

    async def handle(self, message: RegisterView, *, handler: Callable[[Message], Awaitable[None]], **_: Any) -> None:
        # This component doesn't actually need to handle RegisterView messages
        # It just needs to register them during startup
        pass


@dataclass(frozen=True, slots=True, kw_only=True)
class StopProducer(Command): ...


@dataclass(frozen=True, slots=True, kw_only=True)
class ProducerStopped(Event): ...


@dataclass(frozen=True, slots=True, kw_only=True)
class Result(Event):
    value: int


class Producer(Component[StopProducer]):
    """
    Producer sends a message to mediator until it receives stop event.
    """

    def __init__(self, application: System):
        super().__init__(application)
        self._value = 0
        self._finish = False
        self._task: asyncio.Task | None = None

    async def main(self):
        while not self._finish:
            event = Result(value=self._value)
            self._value += 1
            async with self.application.mediator.context() as ctx:
                await ctx.process(event)
                if self._finish:
                    break
            print(f"Produced {event.value}")
            await asyncio.sleep(1.0)
            if self._finish:
                break

    async def on_start(self) -> None:
        self._finish = False
        self._task = asyncio.create_task(self.main())
        await super().on_start()
        self._logger.info("Started")

    async def on_stop(self) -> None:
        self._finish = True
        if self._task:
            await self._task
            self._task = None
        await super().on_stop()
        print(f"{self.__class__.__name__} stopped.")

    async def on_error(self) -> None: ...

    async def handle(
        self,
        message: StopProducer,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        self._finish = True


class Consumer(Component[Result]):
    def __init__(self, system: System, name: str | None = None):
        super().__init__(system)
        self.name = str(type(self)) if name is None else name

    async def on_start(self) -> None:
        print(f"{self.name} started")
        await super().on_start()

    async def on_stop(self) -> None:
        print(f"{self.name} stopped")
        await super().on_stop()

    async def handle(
        self,
        message: Result,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        print(f"{self.name} consumed {message.value}")
        # Only one consumer needs to send StopProducer, but all will receive events.
        if message.value >= 21 and self.name == "Consumer-1":
            await handler(StopProducer())


async def main():
    # single-producer/multi-consumer

    @dataclass(frozen=True, slots=True, kw_only=True)
    class ServerConfig:
        port: int = 8082
        host: str = "localhost"

    config = ServerConfig()
    system = System(configuration=config)

    # Attach components
    system.attach(Producer(system))
    system.attach(Consumer(system, name="Consumer-1"))
    system.attach(Consumer(system, name="Consumer-2"))

    server = Server(system, configuration=config)
    system.attach(server)

    # Add status registration component that will register the view after startup
    system.attach(StatusRegistrationComponent(system, server))

    await system.start()


if __name__ == "__main__":
    try:
        nether.execute(main())
    except KeyboardInterrupt:
        print("Shutting down gracefully")
