"""
Repository pattern for persisting and accessing aggregates from storage.
The storage can be a local file system, in-memory data structure, or a remote database server.

A repository should implement a *transaction* mechanism when possible. However, this cannot always be enforced,
for example, when the underlying storage is an HTTP REST server. In such cases, you may need to implement
*compensation* mechanisms.

There should be one repository per aggregate.
"""

import typing as _t


class Transaction:
  def __aenter__(self) -> _t.Self: ...

  def __aexit__(self) -> _t.Self: ...


class Compensation:
  def __aenter__(self) -> _t.Self: ...

  def __aexit__(self) -> _t.Self: ...


class Repository(_t.Protocol):
  def __init__(self, *_, **__) -> None: ...


class ReporitoryError(Exception): ...


class RevertibleRepository(Repository):
  def __init__(self, *_, **__) -> None:
    super().__init__(_, __)

  def commit(self) -> None: ...

  def revert(self) -> None: ...
