from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol


@dataclass(frozen=True, kw_only=True)
class Message:
  created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))


@dataclass(frozen=True)
class Command(Message): ...


@dataclass(frozen=True)
class Query(Message): ...


@dataclass(frozen=True)
class Event(Message): ...


@dataclass(frozen=True)
class SuccessEvent(Event): ...


@dataclass(frozen=True)
class FailureEvent(Event):
  error: Exception


class ConnectorProtocol[T, C](Protocol):
  def connect(self) -> C: ...

  @contextmanager
  def transaction(self) -> Iterator[T]: ...


class AsyncConnectorProtocol[T, C](Protocol):
  async def connect(self) -> C: ...

  @asynccontextmanager
  def transaction(self) -> AsyncIterator[T]: ...
