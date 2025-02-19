import argparse
import asyncio
import threading
import time
from dataclasses import dataclass
from typing import cast

from arjuna.nether import Application
from arjuna.nether.common import Command
from arjuna.nether.mediator import BaseService, MediatorProtocol
from arjuna.nether.server import HTTPInterfaceService


class MyApplication(Application):
  async def main(self) -> None:
    print("Hello, world!")


@dataclass(frozen=True)
class ProducedCommand(Command):
  number: int = 0


class ProducerService(BaseService[None]):
  def __init__(self):
    self.running_thread: threading.Thread | None = None
    self._stop_event = threading.Event()
    self.mediator = cast(type[MediatorProtocol], None)
    self._is_running = False

  def set_mediator(self, mediator: type[MediatorProtocol]) -> None:
    self.mediator = mediator

  async def _produce_command(self, command: Command) -> None:
    async with self.mediator.open_unit_of_work() as uow:
      await uow.process(command)

  def _worker(self):
    """Worker function that runs in a separate thread."""
    number = 0
    while not self._stop_event.is_set():
      number += 1
      command = ProducedCommand(number)
      print(f"Produced message: {type(command).__name__} {command.number}")
      asyncio.run(self._produce_command(command))
      time.sleep(1)

  async def start(self) -> None:
    print("ProducerService started.")
    self._stop_event.clear()
    self.running_thread = threading.Thread(target=self._worker)
    self.running_thread.daemon = True  # Thread will stop when main program exits
    self.running_thread.start()
    self._is_running = True

  async def stop(self) -> None:
    print("ProducerService stopped.")
    if self.running_thread:
      self._stop_event.set()
      self.running_thread.join()
      self.running_thread = None
    self._is_running = False

  async def handle(self, *_, **__) -> None:
    pass


class ReceiverService(BaseService[ProducedCommand]):
  def __init__(self):
    self.mediator = cast(type[MediatorProtocol], None)
    self._is_running = False

  def set_mediator(self, mediator: type[MediatorProtocol]) -> None:
    self.mediator = mediator

  async def start(self) -> None:
    print("ReceiverService started.")
    self._is_running = True

  async def stop(self) -> None:
    print("ReceiverService stopped.")
    self._is_running = False

  async def handle(self, message: ProducedCommand, **_) -> None:
    print(f"Received message: {type(message).__name__} {message.number}")


async def main():
  configuration = argparse.Namespace()
  configuration.host = "localhost"
  configuration.port = 8080
  server = HTTPInterfaceService(configuration=configuration)

  app = MyApplication(configuration=configuration)
  app.register_service(server)
  app.register_service(ProducerService())
  app.register_service(ReceiverService())
  await app.start()


if __name__ == "__main__":
  asyncio.run(main())
