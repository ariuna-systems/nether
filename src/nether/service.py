from __future__ import annotations
from typing import TYPE_CHECKING, Any, Protocol, get_args
from abc import abstractmethod

if TYPE_CHECKING:
  import asyncio
  from collections.abc import Awaitable, Callable

  from nether.application import Application
  from nether.common import Message


class ServiceProtocol[T: Message](Protocol):
  @property
  def supports(self) -> type[T]:
    """Supported message type."""

  @property
  def is_running(self) -> bool: ...
  def set_application(self, application: Application) -> None: ...
  async def start(self) -> None: ...
  async def stop(self) -> None: ...
  async def handle(
    self,
    message: Message,
    *,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], asyncio.Queue[Any]],
  ) -> None: ...


class BaseService[T: Message](ServiceProtocol[T]):
  def __init__(self, *_, **__) -> None:
    self._is_running = False

  @property
  def supports(self) -> type[T]:
    return get_args(self.__orig_bases__[0])[0]  # type: ignore[attr-defined, no-any-return, unused-ignore]

  @property
  def is_running(self) -> bool:
    return self._is_running

  def set_application(self, application: Application) -> None: ...

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
    join_stream: Callable[[], asyncio.Queue[Any]],
  ) -> None: ...
