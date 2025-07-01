from __future__ import annotations

import asyncio
import contextlib
import logging
import uuid
from typing import TYPE_CHECKING, Any, Protocol, Self

from .common import Command, Event, Message, Query
from .console import configure_logger

if TYPE_CHECKING:
  from collections.abc import AsyncIterator, Awaitable, Callable, Coroutine

  from .application import Application
  from .service import ServiceProtocol
  from .transaction import TransactionContext

logger = logging.getLogger(__name__)
logger.propagate = False
configure_logger(logger)


class MediatorContextProtocol(Protocol):
  def __init__(self, handle_message: Callable[[Message, MediatorContextProtocol], Coroutine[Any, Any, None]] = ...): ...

  @property
  def identifier(self) -> uuid.UUID: ...

  @property
  def tx_context(self) -> TransactionContext: ...

  async def process(self, message: Message) -> None: ...

  async def close(self) -> None: ...

  def join_stream(self) -> tuple[asyncio.Queue[Any], asyncio.Event]: ...

  def add_task(self, task: asyncio.Task[None]) -> None: ...

  async def receive_result(self) -> Event | None: ...


type MediatorContextManager = Callable[[], contextlib.AbstractAsyncContextManager[MediatorContextProtocol]]


class MediatorProtocol(Protocol):
  def set_application(self, application: Application) -> None: ...

  @property
  def services(self) -> set[ServiceProtocol[Any]]: ...

  async def stop(self) -> None: ...

  @contextlib.asynccontextmanager
  def context(self) -> AsyncIterator[MediatorContextProtocol]: ...

  async def register_context(self, context: MediatorContextProtocol) -> None: ...

  async def unregister_context(self, context: MediatorContextProtocol) -> None: ...

  async def handle_message(self, message: Message, context: MediatorContextProtocol) -> None: ...

  async def _handle_global_message(self, message: Message, log_level: int = logging.DEBUG) -> None: ...


class MediatorContext:
  """
  Context manager for a context, providing isolated queues and a database transaction.
  The TransactionContext is provided directly at initialization.
  """

  def __init__(
    self,
    handle_message: Callable[[Message, MediatorContextProtocol], Coroutine[Any, Any, None]],
    tx_context: TransactionContext,  # Direct TransactionContext instance
    logger: logging.Logger,
  ):
    self._handle_message = handle_message
    self._tx_context = tx_context  # Store the provided TransactionContext
    self._id = uuid.uuid4()
    self._results: asyncio.Queue[Event] = asyncio.Queue()
    self._active_tasks: set[asyncio.Task[None]] = set()
    self._stream: asyncio.Queue[Any] = asyncio.Queue()
    self._stream_stop_event: asyncio.Event = asyncio.Event()
    self._logger = logger

  @property
  def identifier(self) -> uuid.UUID:
    return self._id

  @property
  def tx_context(self) -> TransactionContext:
    """Expose the transaction context for handlers."""
    return self._tx_context

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

    await self._tx_context.rollback()
    self._logger.info(f"MediatorContext {self._id} closed.")

  def join_stream(self) -> tuple[asyncio.Queue[Any], asyncio.Event]:
    return (self._stream, self._stream_stop_event)

  async def receive_result(self) -> Event | None:
    """Await and return the next available event for this context."""
    return await self._results.get()


class Mediator:
  """Mediator dispatches messages to handlers."""

  _instance: Self | None = None

  def __new__(cls) -> Self:
    if cls._instance is None:
      cls._instance = super().__new__(cls)
      cls._instance._init_bus()
    return cls._instance

  def _init_bus(self) -> None:
    self._contexts: dict[uuid.UUID, MediatorContextProtocol] = {}
    self._context_locks: dict[uuid.UUID, asyncio.Lock] = {}
    self._application: Application

  def set_application(self, application: Application) -> None:
    self._application = application

  @property
  def application(self) -> Application:
    return self._application

  @contextlib.asynccontextmanager
  async def context(self):
    """
    Classmethod context manager to open a new context
    using the existing mediator instance or creating a new one if needed.
    """
    tx_context = self.application.transaction_manager.context()
    mediator_context = MediatorContext(self.handle_message, tx_context, logger=logger)
    try:
      await self.register_context(mediator_context)
      yield mediator_context
    except Exception:
      raise
    finally:
      await mediator_context.close()
      if mediator_context:
        await self.unregister_context(mediator_context)

  @property
  def services(self) -> set[ServiceProtocol[Any]]:
    return self._application.services

  async def stop(self) -> None:
    self._instance = None

  def _get_context_lock(self, context_id: uuid.UUID) -> asyncio.Lock:
    if context_id not in self._context_locks:
      self._context_locks[context_id] = asyncio.Lock()
    return self._context_locks[context_id]

  async def register_context(self, context: MediatorContextProtocol) -> None:
    """Registers a new context to receive messages."""
    async with self._get_context_lock(context.identifier):
      logger.debug(f"Context `{context.identifier}` registered.")
      self._contexts[context.identifier] = context

  async def unregister_context(self, context: MediatorContextProtocol) -> None:
    """Unregisters a context, stopping message routing to it."""
    async with self._get_context_lock(context.identifier):
      if self._contexts.pop(context.identifier, None) is not None:  # Pop without raising
        logger.debug(f"Context `{context.identifier}` unregistered.")

  @staticmethod
  async def _handling_task(
    *,
    service: ServiceProtocol[Any],
    message: Message,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    tx_context: TransactionContext,
  ) -> None:
    try:
      await service.handle(message, dispatch=dispatch, join_stream=join_stream, tx_context=tx_context)
    except Exception as error:
      logger.critical(f"Uncaught error from {type(service)}: {error}")

  async def handle_message(self, message: Message, context: MediatorContextProtocol) -> None:
    """Handles a message in context by dispatching it to the appropriate services."""
    handled = False
    for service in self.services:
      if isinstance(message, service.supports):
        task = asyncio.create_task(
          Mediator._handling_task(
            service=service,
            message=message,
            dispatch=context.process,
            join_stream=context.join_stream,
            tx_context=context.tx_context,
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

    tx_context = self.application.transaction_manager.context()
    handled = False
    for service in self.services:
      if isinstance(message, service.supports):
        await self._handling_task(
          service=service,
          message=message,
          dispatch=dispatch_to_logger,
          join_stream=lambda: (asyncio.Queue(), asyncio.Event()),
          tx_context=tx_context,
        )
        handled = True

    await tx_context.rollback()
    if not handled:
      logger.critical(f"No handler found for message: {message}")
