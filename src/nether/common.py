import time
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from typing import Protocol


class DomainError(Exception): ...


class ServiceError(Exception): ...


@dataclass(frozen=True, kw_only=True)
class Message:
  created_at: float = field(default_factory=time.time)
  ...


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
  ...


class ConnectorProtocol[T](Protocol):
  @contextmanager
  def transaction(self) -> Iterator[T]: ...


class AsyncConnectorProtocol[T](Protocol):
  @asynccontextmanager
  def transaction(self) -> AsyncIterator[T]: ...
