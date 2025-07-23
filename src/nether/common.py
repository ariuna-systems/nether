from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from typing import Protocol


class ConnectorProtocol[T, C](Protocol):
  def connect(self) -> C: ...

  @contextmanager
  def transaction(self) -> Iterator[T]: ...


class AsyncConnectorProtocol[T, C](Protocol):
  async def connect(self) -> C: ...

  @asynccontextmanager
  def transaction(self) -> AsyncIterator[T]: ...
