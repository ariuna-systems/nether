# This file was renamed from extension.py to component.py
# All classes and references have been updated to use Component terminology.

import asyncio
import logging
from abc import abstractmethod
from collections.abc import Awaitable, Callable
from enum import StrEnum, unique
from typing import Any, Protocol, TypeVar, get_args

from nether.common import Message


class _NeverMatch: ...


@unique
class ComponentState(StrEnum):
  STARTED = "started"
  PENDING = "pending"
  RUNNING = "running"
  STOPPED = "stopped"


class ComponentProtocol[T: Message](Protocol):
  """Component extends a framework with specific functionality
  e.g background processing, system monitoring etc.

  We called it service or module in the past but it can be confusing because it clashes
  with domain driven design terminology or Python naming.
  """

  @property
  def supports(self) -> type[T] | type[_NeverMatch]:
    """Supported message types."""

  @property
  def state(self) -> ComponentState: ...

  @abstractmethod
  async def on_start(self) -> None: ...

  @abstractmethod
  async def on_stop(self) -> None: ...

  @abstractmethod
  async def handle(
    self,
    message: Message,
    *,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
  ) -> None: ...

  # async def main(self): ...


class Component[T: Message](ComponentProtocol[T]):
  def __init__(self, application, *_, logger: logging.Logger | None = None, **__) -> None:
    self.application = application
    if logger is not None:
      self._logger = logger
    else:
      self._logger = logging.getLogger(type(self).__name__)
      self._logger.addHandler(logging.NullHandler())
    self._is_running = False

  @property
  def supports(self) -> type[T] | type[_NeverMatch]:
    supports_type = get_args(self.__orig_bases__[0])[0]  # type: ignore[attr-defined, no-any-return, unused-ignore]
    if isinstance(supports_type, TypeVar):
      return _NeverMatch
    return supports_type

  @property
  def state(self) -> ComponentState:
    return self._is_running  # TODO: return current state

  async def on_start(self) -> None:
    self._state = ComponentState.STARTED

  async def on_stop(self) -> None:
    self._state = ComponentState.STOPPED

  @abstractmethod
  async def handle(
    self,
    message: Message,
    *,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
  ) -> None: ...

  # async def main(self): ...
