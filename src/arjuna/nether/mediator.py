import asyncio
import contextlib
import logging
import sys
import uuid
from abc import abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, Self, get_args

from .common import Command, Event, Message, Query

logger = logging.getLogger(__name__)
logger.propagate = False
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


class ServiceProtocol[T: Message](Protocol):
  @property
  def supports(self) -> type[T]:
    """Supported message type."""

  @property
  def is_running(self) -> bool: ...
  def set_mediator(self, mediator: "type[MediatorProtocol]") -> None: ...
  async def start(self) -> None: ...
  async def stop(self) -> None: ...
  async def handle(
    self,
    message: Message,
    *,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], asyncio.Queue[Any]],
  ) -> None: ...


class UnitOfWorkProtocol(Protocol):
  id: uuid.UUID

  def __init__(self, mediator_class: "type[MediatorProtocol]" = ...): ...
  async def __aenter__(self) -> Self: ...
  async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None: ...

  async def process(self, message: Message) -> None: ...
  async def close(self) -> None: ...
  def join_stream(self) -> asyncio.Queue[Any]: ...
  def add_task(self, task: asyncio.Task[None]) -> None: ...
  async def receive_result(self) -> Event | None: ...


class MediatorProtocol(Protocol):
  @classmethod
  def services(cls) -> set[ServiceProtocol[Any]]: ...
  @classmethod
  async def stop(cls) -> None: ...
  @classmethod
  @contextlib.asynccontextmanager
  async def open_unit_of_work(cls): ...
  async def register_unit_of_work(self, uow: UnitOfWorkProtocol) -> None: ...
  async def unregister_unit_of_work(self, uow: UnitOfWorkProtocol) -> None: ...
  async def handle_message(self, message: Message, uow_id: uuid.UUID) -> None: ...
  async def _handle_global_message(self, message: Message, log_level: int = logging.DEBUG) -> None: ...
  @classmethod
  def register(cls, handler: ServiceProtocol[Any]) -> None: ...
  @classmethod
  def unregister(cls, handler: ServiceProtocol[Any]) -> None: ...


class BaseService[T: Message](ServiceProtocol[T]):
  @property
  def supports(self) -> type[T]:
    return get_args(self.__orig_bases__[0])[0]  # type: ignore[attr-defined, no-any-return, unused-ignore]

  @property
  def is_running(self) -> bool:
    return self._is_running  # type: ignore[attr-defined]

  @abstractmethod
  def set_mediator(self, mediator: "type[MediatorProtocol]") -> None: ...

  @abstractmethod
  async def start(self) -> None: ...

  @abstractmethod
  async def stop(self) -> None: ...

  @abstractmethod
  async def handle(
    self,
    message: Message,
    *,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], asyncio.Queue[Any]],
  ) -> None: ...


class UnitOfWork:
  """Context manager for a unit of work, providing isolated queues."""

  def __init__(self, mediator_class: type[MediatorProtocol]):
    """If mediator not passed, automatically gets the singleton `Mediator` instance"""
    self.mediator = mediator_class()

    self.id = uuid.uuid4()
    self._results: asyncio.Queue[Event] = asyncio.Queue()
    self._active_tasks: set[asyncio.Task[None]] = set()
    self._stream: asyncio.Queue[Any] = asyncio.Queue()

  async def __aenter__(self) -> Self:
    logger.debug(f"Unit of work `{self.id}` created.")
    await self.mediator.register_unit_of_work(self)
    return self

  async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
    await self.close()
    await self.mediator.unregister_unit_of_work(self)
    if exc_type:
      raise exc_value

  async def _graceful_finish(self) -> None:
    while self._active_tasks:
      if self._active_tasks:  # If running tasks, wait for at least one to finish
        _, pending = await asyncio.wait(self._active_tasks, return_when=asyncio.FIRST_COMPLETED)
        self._active_tasks = pending

  async def process(self, message: Message) -> None:
    """Send a message through the bus, where it will be handled."""
    logger.debug(f"Unit of work `{self.id}` processing message: {message}")
    match message:
      case Event():
        await self._results.put(message)
      case Command() | Query():
        self._active_tasks.add(asyncio.create_task(self.mediator.handle_message(message, self.id)))
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
    logger.debug(f"Unit of work {self.id} closed.")

  def join_stream(self) -> asyncio.Queue[Any]:
    return self._stream

  async def receive_result(self) -> Event | None:
    """Await and return the next available event for this unit of work."""
    return await self._results.get()


class Mediator:
  """Shared asynchronous message bus that routes messages to units of work."""

  _instance: Self | None = None
  _services: set[ServiceProtocol[Any]] = set()

  def __new__(cls) -> Self:
    if cls._instance is None:
      cls._instance = super().__new__(cls)
      cls._instance._init_bus()
    return cls._instance  # type: ignore[no-any-return, unused-ignore]

  def _init_bus(self) -> None:
    self._units_of_work: dict[uuid.UUID, UnitOfWorkProtocol] = {}
    self._uow_locks: dict[uuid.UUID, asyncio.Lock] = {}

  @classmethod
  @contextlib.asynccontextmanager
  async def open_unit_of_work(cls):
    """
    Classmethod context manager to open a new `UnitOfWork`
    using the existing mediator instance or creating a new one if needed.
    """
    uow = UnitOfWork(cls)
    await uow.__aenter__()
    try:
      yield uow
    finally:
      await uow.__aexit__(None, None, None)

  @classmethod
  def services(cls) -> set[ServiceProtocol[Any]]:
    return cls._services

  @classmethod
  async def stop(cls) -> None:
    for service in cls._services:
      await service.stop()

    del cls._instance
    del cls._services

  def _get_uow_lock(self, uow_id: uuid.UUID) -> asyncio.Lock:
    if uow_id not in self._uow_locks:
      self._uow_locks[uow_id] = asyncio.Lock()
    return self._uow_locks[uow_id]

  async def register_unit_of_work(self, uow: UnitOfWorkProtocol) -> None:
    """Registers a new unit of work to receive messages."""
    async with self._get_uow_lock(uow.id):
      logger.info(f"Unit of work `{uow.id}` registered.")
      self._units_of_work[uow.id] = uow

  async def unregister_unit_of_work(self, uow: UnitOfWorkProtocol) -> None:
    """Unregisters a unit of work, stopping message routing to it."""
    async with self._get_uow_lock(uow.id):
      if self._units_of_work.pop(uow.id, None) is not None:  # Pop without raising
        logger.info(f"Unit of work `{uow.id}` unregistered.")

  @staticmethod
  async def _handler_task(
    *,
    handler: ServiceProtocol[Any],
    message: Message,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], asyncio.Queue[Any]],
  ) -> None:
    try:
      await handler.handle(message, dispatch=dispatch, join_stream=join_stream)
    except Exception as error:
      logger.critical(f"Uncaught error from {type(handler)}: {error}")

  async def handle_message(self, message: Message, uow_id: uuid.UUID) -> None:
    """Handles a message by dispatching it to the appropriate handlers."""
    uow = self._units_of_work.get(uow_id)
    if uow is None:
      return

    handled = False
    for handler in self._services:
      if isinstance(message, handler.supports):
        task = asyncio.create_task(
          self._handler_task(handler=handler, message=message, dispatch=uow.process, join_stream=uow.join_stream)
        )
        uow.add_task(task)
        handled = True

    if not handled:
      logger.critical(f"No handler found for message: {message}")

  async def _handle_global_message(self, message: Message, log_level: int = logging.DEBUG) -> None:
    """Handles a message by dispatching it to the appropriate handlers."""

    async def logger_enqueue(message: Message) -> None:
      logger.log(log_level, f"Global message: {message}")

    handled = False
    for handler in self._services:
      if isinstance(message, handler.supports):
        await self._handler_task(
          handler=handler, message=message, dispatch=logger_enqueue, join_stream=lambda: asyncio.Queue()
        )
        handled = True

    if not handled:
      logger.critical(f"No handler found for message: {message}")

  @classmethod
  def register(cls, handler: ServiceProtocol[Any]) -> None:
    """Register an asynchronous handler."""
    logger.info(f"Handler {type(handler).__name__} registered.")
    cls._services.add(handler)

  @classmethod
  def unregister(cls, handler: ServiceProtocol[Any]) -> None:
    """Unregister an asynchronous handler."""
    logger.info(f"Handler {type(handler).__name__} unregistered.")
    cls._services.remove(handler)
