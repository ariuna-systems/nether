import asyncio
import contextlib
import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Coroutine
from typing import Any, Protocol, Self

from nether.service import ServiceProtocol

from .common import Command, Event, Message, Query
from .console import configure_logger

logger = logging.getLogger(__name__)
logger.propagate = False
configure_logger(logger)


class MediatorContextProtocol(Protocol):
  def __init__(
    self, handle_message: Callable[[Message, "MediatorContextProtocol"], Coroutine[Any, Any, None]] = ...
  ): ...

  @property
  def identifier(self) -> uuid.UUID: ...

  async def process(self, message: Message) -> None: ...

  async def close(self) -> None: ...

  def join_stream(self) -> tuple[asyncio.Queue[Any], asyncio.Event]: ...

  def add_task(self, task: asyncio.Task[None]) -> None: ...

  async def receive_result(self) -> Event | None: ...


type MediatorContextManager = Callable[[], contextlib.AbstractAsyncContextManager[MediatorContextProtocol]]


class MediatorProtocol(Protocol):
  @property
  def services(self) -> set[ServiceProtocol[Any]]: ...

  async def stop(self) -> None: ...

  @contextlib.asynccontextmanager
  def context(self) -> AsyncIterator[MediatorContextProtocol]: ...

  async def register_context(self, context: MediatorContextProtocol) -> None: ...

  async def unregister_context(self, context: MediatorContextProtocol) -> None: ...

  async def handle_message(self, message: Message, context: MediatorContextProtocol) -> None: ...

  async def _handle_global_message(self, message: Message, log_level: int = logging.DEBUG) -> None: ...

  def register(self, service: ServiceProtocol[Any]) -> None: ...

  def unregister(self, service: ServiceProtocol[Any]) -> None: ...


class MediatorContext:
  """Context manager for a unit of work, providing isolated queues."""

  def __init__(self, handle_message: Callable[[Message, MediatorContextProtocol], Coroutine[Any, Any, None]]):
    """If mediator is not passed, automatically gets the singleton :class:`Mediator` instance."""
    self._handle_message = handle_message

    self._id = uuid.uuid4()
    self._results: asyncio.Queue[Event] = asyncio.Queue()
    self._active_tasks: set[asyncio.Task[None]] = set()
    self._stream: asyncio.Queue[Any] = asyncio.Queue()
    self._stream_stop_event: asyncio.Event = asyncio.Event()

  @property
  def identifier(self) -> uuid.UUID:
    return self._id

  async def _graceful_finish(self) -> None:
    while self._active_tasks:
      if self._active_tasks:  # If running tasks, wait for at least one to finish
        _, pending = await asyncio.wait(self._active_tasks, return_when=asyncio.FIRST_COMPLETED)
        self._active_tasks = pending

  async def process(self, message: Message) -> None:
    """Send a message through the bus, where it will be handled."""
    logger.debug(f"Unit of work `{self._id}` processing message: {message}")
    match message:
      case Event():
        await self._results.put(message)
      case Command() | Query():
        self._active_tasks.add(asyncio.create_task(self._handle_message(message, self)))
      case _:
        logger.error(f"Invalid message type: {type(message)}")

  def add_task(self, task: asyncio.Task[None]) -> None:
    self._active_tasks.add(task)

  async def close(self) -> None:
    """Gracefully finish processing and cancel leftover tasks."""
    await self._graceful_finish()
    for task in self._active_tasks:
      if not task.done():
        task.cancel()
    logger.debug(f"Unit of work {self._id} closed.")

  def join_stream(self) -> tuple[asyncio.Queue[Any], asyncio.Event]:
    return (self._stream, self._stream_stop_event)

  async def receive_result(self) -> Event | None:
    """Await and return the next available event for this unit of work."""
    return await self._results.get()


class Mediator:
  """Mediator dispatches messages to handlers."""

  _instance: Self | None = None

  def __new__(cls) -> Self:
    if cls._instance is None:
      cls._instance = super().__new__(cls)
      cls._instance._init_bus()
    return cls._instance  # type: ignore[no-any-return, unused-ignore]

  def _init_bus(self) -> None:
    self._services: set[ServiceProtocol[Any]] = set()
    self._contexts: dict[uuid.UUID, MediatorContextProtocol] = {}
    self._context_locks: dict[uuid.UUID, asyncio.Lock] = {}

  @contextlib.asynccontextmanager
  async def context(self):
    """
    Classmethod context manager to open a new `UnitOfWork`
    using the existing mediator instance or creating a new one if needed.
    """
    context = MediatorContext(self.handle_message)
    await self.register_context(context)
    try:
      yield context
    finally:
      await context.close()
      await self.unregister_context(context)

  @property
  def services(self) -> set[ServiceProtocol[Any]]:
    return self._services

  async def stop(self) -> None:
    logger.info("deleted services")
    for service in self._services:
      await service.stop()
    del self._services
    self._instance = None

  def _get_context_lock(self, context_id: uuid.UUID) -> asyncio.Lock:
    if context_id not in self._context_locks:
      self._context_locks[context_id] = asyncio.Lock()
    return self._context_locks[context_id]

  async def register_context(self, context: MediatorContextProtocol) -> None:
    """Registers a new unit of work to receive messages."""
    async with self._get_context_lock(context.identifier):
      logger.debug(f"Unit of work `{context.identifier}` registered.")
      self._contexts[context.identifier] = context

  async def unregister_context(self, context: MediatorContextProtocol) -> None:
    """Unregisters a unit of work, stopping message routing to it."""
    async with self._get_context_lock(context.identifier):
      if self._contexts.pop(context.identifier, None) is not None:  # Pop without raising
        logger.debug(f"Unit of work `{context.identifier}` unregistered.")

  @staticmethod
  async def _handling_task(
    *,
    service: ServiceProtocol[Any],
    message: Message,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
  ) -> None:
    try:
      await service.handle(message, dispatch=dispatch, join_stream=join_stream)
    except Exception as error:
      logger.critical(f"Uncaught error from {type(service)}: {error}")

  async def handle_message(self, message: Message, context: MediatorContextProtocol) -> None:
    """Handles a message in unit of work by dispatching it to the appropriate services."""
    handled = False
    for service in self._services:
      if isinstance(message, service.supports):
        task = asyncio.create_task(
          self._handling_task(
            service=service, message=message, dispatch=context.process, join_stream=context.join_stream
          )
        )
        context.add_task(task)
        handled = True

    if not handled:
      logger.critical(f"No handler found for message: {message}")

  async def _handle_global_message(self, message: Message, log_level: int = logging.DEBUG) -> None:
    """Handles a global message by dispatching it to the appropriate services."""

    async def dispatch_to_logger(message: Message) -> None:
      """Dispatch function mock for logging."""
      logger.log(log_level, f"Global message: {message}")

    handled = False
    for service in self._services:
      if isinstance(message, service.supports):
        await self._handling_task(
          service=service,
          message=message,
          dispatch=dispatch_to_logger,
          join_stream=lambda: (asyncio.Queue(), asyncio.Event()),
        )
        handled = True

    if not handled:
      logger.critical(f"No handler found for message: {message}")

  def register(self, service: ServiceProtocol[Any]) -> None:
    """Register a service."""
    logger.info(f"Service {type(service).__name__} registered.")
    self._services.add(service)

  def unregister(self, service: ServiceProtocol[Any]) -> None:
    """Unregister a service."""
    logger.info(f"Service {type(service).__name__} unregistered.")
    self._services.remove(service)
