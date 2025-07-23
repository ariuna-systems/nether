"""
Mediator pattern for in-process, asynchronous message routing.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Coroutine
from typing import Any, Protocol, Self

from .component import ComponentProtocol
from .logging import configure_logger
from .message import Command, Event, Message, Query

__all__ = [
  "Context",
  "ContextManager",
  "ContextProtocol",
  "Mediator",
  "MediatorProtocol",
]


logger = logging.getLogger(__name__)
logger.propagate = False

configure_logger(logger)


class ContextProtocol(Protocol):
  def __init__(self, handle_message: Callable[[Message, Self], Coroutine[Any, Any, None]] = ...): ...

  @property
  def identifier(self) -> uuid.UUID: ...

  async def process(self, message: Message) -> None: ...

  async def close(self) -> None: ...

  async def join_stream(self) -> tuple[asyncio.Queue[Any], asyncio.Event]: ...

  async def add_task(self, task: asyncio.Task[None]) -> None: ...

  async def receive_result(self) -> Event | None: ...


type ContextManager = Callable[[], contextlib.AbstractAsyncContextManager[ContextProtocol]]


class Context:
  """Context represents a unit of work, providing isolated queues."""

  def __init__(
    self,
    handle_message: Callable[[Message, ContextProtocol], Coroutine[Any, Any, None]],
  ):
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
    self._logger.debug(f"Context `{self._id}` processing message: {message}")
    match message:
      case Event():
        await self._results.put(message)
        # Also dispatch Events to modules that can handle them
        self._active_tasks.add(asyncio.create_task(self._handle_message(message, self)))
      case Command() | Query():
        self._active_tasks.add(asyncio.create_task(self._handle_message(message, self)))
      case _:
        self._logger.error(f"Invalid message type: {type(message)}")

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

  def join_stream(self) -> tuple[asyncio.Queue[Any], asyncio.Event]:
    return (self._stream, self._stream_stop_event)

  async def receive_result(self) -> Event | None:
    """Await and return the next available event for this context."""
    return await self._results.get()


class MediatorProtocol(Protocol):
  @property
  def modules(self) -> set[ComponentProtocol[Any]]: ...

  async def stop(self) -> None: ...

  @contextlib.asynccontextmanager
  async def context(self) -> AsyncIterator[ContextProtocol]: ...

  async def register_context(self, context: ContextProtocol) -> None: ...

  async def unregister_context(self, context: ContextProtocol) -> None: ...

  async def handle_message(self, message: Message, context: ContextProtocol) -> None: ...

  async def register_module(self, module: ComponentProtocol[Any]) -> None: ...

  async def unregister_module(self, module: ComponentProtocol[Any]) -> None: ...


class Mediator:
  """Mediator dispatches messages to handlers."""

  _instance: Self | None = None

  def __new__(cls) -> Self:
    if cls._instance is None:
      cls._instance = super().__new__(cls)
      cls._instance.__init_bus()
    return cls._instance  # type: ignore[no-any-return, unused-ignore]

  def __init_bus(self) -> None:
    self._modules: set[ComponentProtocol[Any]] = set()
    self._contexts: dict[uuid.UUID, ContextProtocol] = {}
    self._context_locks: dict[uuid.UUID, asyncio.Lock] = {}

  @contextlib.asynccontextmanager
  async def context(self):
    """
    The class method context manager to open a new unit-of-work
    using the existing mediator instance or creating a new one if needed.
    """
    context = Context(self.handle)
    await self.register_context(context)
    try:
      await self.register_context(context)
      yield context
    except Exception:
      raise
    finally:
      await context.close()
      if context:
        await self.unregister_context(context)

  @property
  def modules(self) -> set[ComponentProtocol[Any]]:
    if not hasattr(self, "_modules"):
      self.__init_bus()
    return self._modules

  async def stop(self) -> None:
    logger.info("deleted services")
    for module in self._modules:
      await module.on_stop()
    del self._modules
    self._instance = None

  def _get_context_lock(self, context_id: uuid.UUID) -> asyncio.Lock:
    if context_id not in self._context_locks:
      self._context_locks[context_id] = asyncio.Lock()
    return self._context_locks[context_id]

  async def register_context(self, context: ContextProtocol) -> None:
    """Registers a new unit of work to receive messages."""
    async with self._get_context_lock(context.identifier):
      logger.debug(f"Context `{context.identifier}` registered.")
      self._contexts[context.identifier] = context

  async def unregister_context(self, context: ContextProtocol) -> None:
    """Unregisters a unit of work, stopping message routing to it."""
    async with self._get_context_lock(context.identifier):
      if self._contexts.pop(context.identifier, None) is not None:  # Pop without raising
        logger.debug(f"Context `{context.identifier}` unregistered.")

  @staticmethod
  async def _handling_task(
    *,
    module: ComponentProtocol[Any],
    message: Message,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
  ) -> None:
    try:
      await module.handle(message, dispatch=dispatch, join_stream=join_stream)
    except Exception as error:
      logger.critical(f"Uncaught error from {type(module)}: {error}")

  async def handle(self, message: Message, context: ContextProtocol) -> None:
    """Handles a message in unit of work by dispatching it to the appropriate modules."""
    handled = False
    for module in self._modules:
      if isinstance(message, module.supports):
        task = asyncio.create_task(
          self._handling_task(
            module=module,
            message=message,
            dispatch=context.process,
            join_stream=context.join_stream,
          )
        )
        context.add_task(task)
        handled = True

    if not handled:
      logger.critical(f"No handler found for message: {message}")

  def register_module(self, module: ComponentProtocol[Any]) -> None:
    """Register a service."""
    logger.info(f"Module {type(module).__name__} registered.")
    self._modules.add(module)

  def unregister_module(self, module: ComponentProtocol[Any]) -> None:
    """Unregister a service."""
    logger.info(f"module {type(module).__name__} unregistered.")
    self._modules.remove(module)
