# This file was renamed from extension.py to component.py
# All classes and references have been updated to use Component terminology.

import asyncio
import logging
from abc import abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Any, TypeVar, get_args

from nether.message import Command, Message


class _NeverMatch: ...


@unique
class ComponentState(StrEnum):
  STARTED = "started"
  PENDING = "pending"
  RUNNING = "running"
  STOPPED = "stopped"


@dataclass(frozen=True, slots=True, kw_only=True)
class ComponentPauseExecution(Command): ...


@dataclass(frozen=True, slots=True, kw_only=True)
class ComponentResumeExecution(Command): ...


class Component[T: type[Message] | tuple[type[Message], ...]]:
  """Component extends a framework with specific functionality
  e.g background processing, system monitoring etc.

  * Component can handle specified type of signals with :meth:`handle` method.
  * Componnet has a lifecycle and state, can be started, paused, resumed or stopped.
  * Component has initilization and finilization phase.

  .. note: It can be called service or module but it is confusing because it clashes
  with Python and Domain-Driven Design terminology.
  """

  def __init__(self, application, *_, logger: logging.Logger | None = None, **__) -> None:
    self.application = application
    if logger is not None:
      self._logger = logger
    else:
      self._logger = logging.getLogger(type(self).__name__)
      self._logger.addHandler(logging.NullHandler())
    self._is_running = False

  @property
  def supports(self) -> type[Message] | tuple[type[Message], ...] | type[_NeverMatch]:
    supports_type = get_args(self.__orig_bases__[0])[0]  # type: ignore[attr-defined, no-any-return, unused-ignore]
    if isinstance(supports_type, TypeVar):
      return _NeverMatch
    return supports_type

  @property
  def state(self) -> ComponentState:
    return self._is_running  # TODO: return current state

  async def on_start(self) -> None:
    """Called when a component is in initializing phase."""
    self._state = ComponentState.STARTED

  async def on_stop(self) -> None:
    """Called when a component is in finalizing phase."""
    self._state = ComponentState.STOPPED

  async def on_error(self) -> None: ...

  @abstractmethod
  async def handle(
    self,
    message: T,
    *,
    callback: Callable[[T], Awaitable[None]],
    channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
  ) -> None: ...

  async def main(self):
    """The main component work."""
