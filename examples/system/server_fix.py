"""
Monkey patch to fix the nether server bug where StartServer and StopServer
messages are not handled in the handle method.
"""

from typing import Any, Awaitable, Callable

from nether.message import Message
from nether.server import (
    Server,
    ServerStarted,
    ServerStopped,
    StartServer,
    StartServerFailure,
    StopServer,
    StopServerFailure,
)


# Store the original handle method
_original_handle = Server.handle


async def fixed_handle(
    self, message: Message, *, handler: Callable[[Message], Awaitable[None]], **_: Any
) -> None:
    """Fixed handle method that properly handles StartServer and StopServer messages."""
    if not isinstance(message, self.supports):
        return

    result_event = None
    try:
        match message:
            case StartServer():
                # Check if server is already running to avoid duplicate starts
                if not self._is_running:
                    await self.on_start()
                result_event = ServerStarted()
            case StopServer():
                # Check if server is actually running before stopping
                if self._is_running:
                    await self.on_stop()
                result_event = ServerStopped()
            case _:
                # For other message types, delegate to the original handle method
                # But we need to handle RegisterView and AddStatic here too since
                # the original method has the same bug
                from nether.server import (
                    AddStatic,
                    AddStaticFailure,
                    RegisterView,
                    RegisterViewFailure,
                    StaticAdded,
                    ViewRegistered,
                )

                match message:
                    case RegisterView():
                        await self._add_view(route=message.route, view=message.view)
                        result_event = ViewRegistered()
                    case AddStatic():
                        await self._add_static(
                            prefix=message.prefix, path=message.path, **message.kwargs
                        )
                        result_event = StaticAdded()

    except Exception as error:
        match message:
            case StartServer():
                result_event = StartServerFailure(error=error)
            case StopServer():
                result_event = StopServerFailure(error=error)
            case _:
                from nether.server import AddStaticFailure, RegisterViewFailure

                match message:
                    case RegisterView():
                        result_event = RegisterViewFailure(error=error)
                    case AddStatic():
                        result_event = AddStaticFailure(error=error)
    finally:
        if result_event is not None:
            await handler(result_event)


# Apply the monkey patch
Server.handle = fixed_handle

print("Applied monkey patch to fix nether server StartServer/StopServer handling bug")
