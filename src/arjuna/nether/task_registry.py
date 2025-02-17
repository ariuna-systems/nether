import asyncio
import uuid
from typing import Any

# TODO: Implement the TaskRegistry class, bind tasks to the application
class TaskRegistry:
  def __init__(self):
    self._tasks: dict[uuid.UUID, set[asyncio.Task[Any]]] = {}
    self._closed: bool = False

  def add_uow(self, uow_id: uuid.UUID) -> None:
    if uow_id not in self._tasks:
      self._tasks[uow_id] = set()

  def remove_uow(self, uow_id: uuid.UUID) -> None:
    self._tasks.pop(uow_id, None)

  def register(self, task: asyncio.Task[Any], uow_id: uuid.UUID) -> None:
    if self._closed:
      task.cancel()
    else:
      self._tasks[uow_id].add(task)

  def stop_all(self) -> None:
    self._closed = True
    for tasks in self._tasks.values():
      for task in tasks:
        task.cancel()
