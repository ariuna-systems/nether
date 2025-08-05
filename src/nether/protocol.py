from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from typing import Protocol


class ConnectorProtocol[T, C](Protocol):
  """FIXME What is this for?"""

  def connect(self) -> C: ...

  @contextmanager
  def transaction(self) -> Iterator[T]: ...


class AsyncConnectorProtocol[T, C](Protocol):
  """FIXME What is this for?"""

  async def connect(self) -> C: ...

  @asynccontextmanager
  def transaction(self) -> AsyncIterator[T]: ...
