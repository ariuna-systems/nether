import asyncio
import logging
from abc import abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, TypeVar, get_args

from .common import Message
from .transaction import TransactionContext


class _NeverMatch: ...


class ServiceProtocol[T: Message](Protocol):
  @property
  def supports(self) -> type[T] | type[_NeverMatch]:
    """Supported message type."""

  @property
  def is_running(self) -> bool: ...

  def set_application(self, application) -> None: ...

  async def start(self) -> None: ...

  async def stop(self) -> None: ...

  async def handle(
    self,
    message: Message,
    *,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    tx_context: TransactionContext,
  ) -> None: ...


class Service[T: Message](ServiceProtocol[T]):
  def __init__(self, *_, logger: logging.Logger | None = None, **__) -> None:
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
  def is_running(self) -> bool:
    return self._is_running

  def set_application(self, application) -> None: ...

  async def start(self) -> None:
    self._is_running = True

  async def stop(self) -> None:
    self._is_running = False

  @abstractmethod
  async def handle(
    self,
    message: Message,
    *,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    tx_context: TransactionContext,
  ) -> None: ...
