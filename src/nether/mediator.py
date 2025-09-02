"""
Mediator for in-process asynchronous message routing and handling.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any, Self

from .component import Component
from .message import Command, Event, Message, Query

__all__ = [
    "Context",
    "Mediator",
]


logger = logging.getLogger(__name__)


class Context:
    """Context represents a unit of work, providing isolated queues."""

    def __init__(
        self,
        handle_message: Callable[[Message, Self], Coroutine[Any, Any, None]],
    ) -> None:
        """If mediator is not passed, automatically gets the singleton :class:`Mediator` instance."""
        self._handle_message = handle_message
        self._id = uuid.uuid4()
        self._results: asyncio.Queue[Event] = asyncio.Queue()
        self._active_tasks: set[asyncio.Task[None]] = set()
        self._stream: asyncio.Queue[Any] = asyncio.Queue()
        self._stream_stop_event: asyncio.Event = asyncio.Event()
        self._logger = logger

    @property
    def identifier(self) -> uuid.UUID:
        return self._id

    async def _graceful_finish(self) -> None:
        while self._active_tasks:
            tasks_to_wait_for = list(self._active_tasks)
            await asyncio.gather(*tasks_to_wait_for, return_exceptions=True)
            self._active_tasks.difference_update(tasks_to_wait_for)

    async def process(self, message: Message) -> None:
        """Send a message through the bus, where it will be handled."""
        self._logger.info(f"Context `{self._id}` processing message: {type(message).__name__} - {message}")
        self._logger.debug(f"Context `{self._id}` message details: {message}")
        match message:
            case Event():
                await self._results.put(message)
                self._active_tasks.add(asyncio.create_task(self._handle_message(message, self)))
                self._logger.debug(f"Context `{self._id}` queued event: {type(message).__name__}")
            case Command() | Query():
                self._active_tasks.add(asyncio.create_task(self._handle_message(message, self)))
                self._logger.debug(f"Context `{self._id}` dispatched {type(message).__name__}")
            case _:
                self._logger.error(f"Context `{self._id}` - Invalid message type: {type(message)}")
                raise ValueError(f"Invalid message type: {type(message)}")

    def add_task(self, task: asyncio.Task[None]) -> None:
        self._active_tasks.add(task)

    async def close(self) -> None:
        """
        Gracefully finish processing, cancel leftover tasks,
        and rollback the associated transaction if not already committed.
        """
        self._logger.info(f"MediatorContext {self._id} closing. Finishing active tasks...")
        await self._graceful_finish()
        for task in self._active_tasks:
            if not task.done():
                task.cancel()

        self._logger.info(f"MediatorContext {self._id} closed.")

    def channel(self) -> tuple[asyncio.Queue[Any], asyncio.Event]:
        return (self._stream, self._stream_stop_event)

    async def receive_result(self) -> Event | None:
        """Await and return the next available event for this context."""
        return await self._results.get()


class Mediator:
    """Mediator routes messages to registered components that handles messages.
    This allows decoupled asynchronous communication between components.
    """

    _instance: Self | None = None
    _initialized: bool = False

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance  # type: ignore[no-any-return, unused-ignore]

    def __init__(self) -> None:
        """Initialize the singleton mediator instance only once."""
        if not self._initialized:
            self._contexts: dict[uuid.UUID, Context] = {}
            self._context_locks: dict[uuid.UUID, asyncio.Lock] = {}
            self._components: set[Component[Any]] = set()
            self._initialized = True

    @asynccontextmanager
    async def context(self):
        """
        Context manager to start a new unit-of-work using the mediator instance.
        Registers the context, yields it, and ensures cleanup on exit.
        """
        context = Context(self.handle)
        await self.attach_context(context)
        try:
            yield context
        finally:
            await context.close()
            await self.detach_context(context)

    @property
    def components(self) -> set[Component[Any]]:
        """Get the set of registered components."""
        return self._components

    async def stop(self) -> None:
        """Stop all registered services and reset singleton state."""
        logger.info(f"{self.__class__.__name__} stopping")
        for component in self.components:
            await component.on_stop()

        # Reset singleton state for clean restart
        self._components.clear()
        self._contexts.clear()
        self._context_locks.clear()
        self.__class__._initialized = False
        self.__class__._instance = None

    def _get_context_lock(self, context_id: uuid.UUID) -> asyncio.Lock:
        if context_id not in self._context_locks:
            self._context_locks[context_id] = asyncio.Lock()
        return self._context_locks[context_id]

    def attach(self, component: Component[Any]) -> None:
        """Attach and register a component.
        :param component: The component to add to registered components.
        """
        component_name = type(component).__name__
        self._components.add(component)
        logger.info(f"Component {component_name} attached (supports: {component.supports})")

    def detach(self, component: Component[Any]) -> None:
        """Detach and unregister a component.
        :param component: The component to remove from registered components.
        """
        component_name = type(component).__name__
        if component in self._components:
            self._components.remove(component)
            logger.info(f"Component {component_name} detached")
        else:
            logger.warning(f"Attempted to detach non-registered component {component_name}")

    async def attach_context(self, context: Context) -> None:
        """Registers a new unit of work to receive messages."""
        async with self._get_context_lock(context.identifier):
            logger.info(f"Attaching context `{context.identifier}`")
            self._contexts[context.identifier] = context

    async def detach_context(self, context: Context) -> None:
        """Unregisters a unit of work, stopping message routing to it."""
        async with self._get_context_lock(context.identifier):
            if self._contexts.pop(context.identifier, None) is not None:
                logger.info(f"Detached context `{context.identifier}`")
            else:
                logger.warning(f"Attempted to detach non-existent context `{context.identifier}`")

    async def handle(self, message: Message, context: Context = None) -> None:
        """
        Handles a message in the specified context (unit-of-work).
        """

        async def _handle(
            *,
            module: Component[Any],
            message: Message,
            handler: Callable[[Message], Awaitable[None]],
            channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
        ) -> None:
            component_name = type(module).__name__
            message_type = type(message).__name__
            logger.debug(f"Handling {message_type} with component {component_name}")
            try:
                await module.handle(message, handler=handler, channel=channel)
                logger.debug(f"Successfully handled {message_type} with {component_name}")
            except Exception as error:
                logger.critical(f"Uncaught error from {component_name} handling {message_type}: {error}")
                logger.debug(f"Error details for {component_name}: {error}", exc_info=True)

        async def dispatch(message: Message, context: Context) -> None:
            message_type = type(message).__name__
            logger.info(f"Dispatching {message_type}: {message}")
            handled = False
            matching_components = []

            for module in self.components:
                supports = module.supports
                if isinstance(supports, tuple):
                    match_type = any(isinstance(message, t) for t in supports)
                else:
                    match_type = isinstance(message, supports)

                if match_type:
                    matching_components.append(type(module).__name__)

                    async def simple_handler(msg: Message) -> None:
                        # Non recursive handle callback.
                        logger.debug(f"Simple handler processing: {type(msg).__name__}")
                        await context.process(msg)

                    task = asyncio.create_task(
                        _handle(
                            module=module,
                            message=message,
                            handler=simple_handler,
                            channel=context.channel,
                        )
                    )
                    context.add_task(task)
                    handled = True

            if handled:
                logger.info(f"Message {message_type} dispatched to components: {', '.join(matching_components)}")
            else:
                logger.critical(f"Handler not found for message {message_type}: {message}")

        if context is None:
            async with self.context() as context:
                logger.info(f"[MEDIATOR-IN] {type(message).__name__}: {message}")
                await dispatch(message, context)
                logger.info(f"[MEDIATOR-OUT] {type(message).__name__} processing completed")
        else:
            await dispatch(message, context)
