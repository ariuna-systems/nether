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
from .logging import configure_logger
from .message import Command, Event, Message, Query

__all__ = [
  "Context",
  "Mediator",
]


logger = logging.getLogger(__name__)
logger.propagate = False

configure_logger(logger)


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
    self._logger.debug(f"Context `{self._id}` processing message: {message}")
    match message:
      case Event():
        await self._results.put(message)
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
    self._components.add(component)
    logger.info(f"component {type(component).__name__} attached")

  def detach(self, component: Component[Any]) -> None:
    """Detach and unregister a component.
    :param component: The component to remove from registered components.
    """
    self._components.remove(component)
    logger.info(f"component {type(component).__name__} detached")

  async def attach_context(self, context: Context) -> None:
    """Registers a new unit of work to receive messages."""
    async with self._get_context_lock(context.identifier):
      logger.debug(f"context `{context.identifier}` attached")
      self._contexts[context.identifier] = context

  async def detach_context(self, context: Context) -> None:
    """Unregisters a unit of work, stopping message routing to it."""
    async with self._get_context_lock(context.identifier):
      if self._contexts.pop(context.identifier, None) is not None:
        logger.debug(f"context `{context.identifier}` detached")

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
      try:
        await module.handle(message, handler=handler, channel=channel)
      except Exception as error:
        logger.critical(f"Uncaught error from {type(module)}: {error}")

    async def dispatch(message: Message, context: Context) -> None:
      handled = False

      for module in self.components:
        supports = module.supports
        if isinstance(supports, tuple):
          match_type = any(isinstance(message, t) for t in supports)
        else:
          match_type = isinstance(message, supports)
        if match_type:

          async def simple_handler(msg: Message) -> None:
            # Non recursive handle callback.
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
      if not handled:
        logger.critical(f"Handler not found for message {message}")

    if context is None:
      async with self.context() as context:
        logger.info(f"[?] {message}")  # TODO: SAVE TO AUDIT LOG
        await dispatch(message, context)
        logger.info(f"[!] {message}")  # TODO: SAVE TO AUDIT LOG
    else:
      await dispatch(message, context)
