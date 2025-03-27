import argparse
import asyncio
import threading
import time
from dataclasses import dataclass
from typing import cast

from nether import Application
from nether.common import Command
from nether.mediator import MediatorProtocol
from nether.server import HTTPInterfaceService
from nether.service import BaseService


class MyApplication(Application):
  async def main(self) -> None:
    print("Hello, world!")


@dataclass(frozen=True)
class ProducedCommand(Command):
  number: int = 0


class ProducerService(BaseService):
  def __init__(self):
    super().__init__(self)
    self.running_thread: threading.Thread | None = None
    self._stop_event = threading.Event()
    self._application = cast(Application, None)

  def set_application(self, application: Application) -> None:
    self._application = application

  async def _produce_command(self, command: Command) -> None:
    async with self._application.mediator.context() as ctx:
      await ctx.process(command)

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
    super().__init__(self)
    self.mediator = cast(type[MediatorProtocol], None)

  def set_application(self, application: Application) -> None:
    self._application = application

  async def start(self) -> None:
    print("ReceiverService started.")
    self._is_running = True

  async def stop(self) -> None:
    print("ReceiverService stopped.")
    self._is_running = False

  async def handle(self, message, **_) -> None:
    print(f"Received message: {type(message).__name__} {message.number}")


class ErrorRaisingService(BaseService):
  def __init__(self):
    super().__init__(self)

  async def start(self) -> None:
    print("ErrorRaisingService started.")
    raise Exception("ErrorRaisingService error")
    self._is_running = True

  async def stop(self) -> None:
    print("ErrorRaisingService stopped.")
    self._is_running = False

  async def handle(self, *_, **__) -> None:
    raise Exception("ErrorRaisingService error")


async def main():
  configuration = argparse.Namespace()
  configuration.host = "localhost"
  configuration.port = 8080
  server = HTTPInterfaceService(configuration=configuration)

  app = MyApplication(configuration=configuration)
  app.register_service(server)
  app.register_service(ProducerService())
  app.register_service(ReceiverService())
  app.register_service(ErrorRaisingService())
  await app.start()


if __name__ == "__main__":
  asyncio.run(main())
