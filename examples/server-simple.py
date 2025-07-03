import argparse
import asyncio
import logging
from dataclasses import dataclass
from typing import cast

from nether import Application
from nether.common import Command
from nether.console import configure_logger
from nether.mediator import MediatorProtocol
from nether.server import HTTPInterfaceService
from nether.service import Service
from nether.transaction import TransactionContext

logger = logging.getLogger(__name__)
configure_logger(logger, 1)


class MyApplication(Application):
  async def main(self) -> None:
    print("Hello, world!")


@dataclass(frozen=True)
class ProducedCommand(Command):
  number: int = 0


class ProducerService(Service):
  def __init__(self):
    super().__init__(self)
    self._stop_event = asyncio.Event()  # Use asyncio.Event for async coordination
    self._application = cast(Application, None)
    self._producer_task: asyncio.Task | None = None  # To hold the background task

  def set_application(self, application: Application) -> None:
    self._application = application

  async def _produce_command(self, command: Command) -> None:
    async with self._application.mediator.context() as ctx:
      await ctx.process(command)

  async def _worker(self):  # Make _worker an async function
    """Worker coroutine that runs in the main event loop."""
    number = 0
    while not self._stop_event.is_set():
      number += 1
      command = ProducedCommand(number)
      logger.info(f"Produced message: {type(command).__name__} {command.number}")
      asyncio.create_task(self._produce_command(command))  # Await the async call directly
      try:
        await asyncio.sleep(1)  # Use asyncio.sleep for non-blocking delay
      except asyncio.CancelledError:
        logger.info("ProducerService worker cancelled.")
        break

  async def start(self) -> None:
    logger.info("ProducerService started.")
    self._stop_event.clear()
    # Start the _worker as a background task in the current event loop
    self._producer_task = asyncio.create_task(self._worker())
    self._is_running = True

  async def stop(self) -> None:
    logger.info("ProducerService stopped.")
    if self._producer_task:
      self._stop_event.set()  # Signal the worker to stop gracefully
      self._producer_task.cancel()  # Request cancellation of the task
      try:
        await self._producer_task  # Await its completion to clean up
      except asyncio.CancelledError:
        pass  # Expected when we cancel it
      self._producer_task = None
    self._is_running = False

  async def handle(self, *_, **__) -> None:
    pass


class ReceiverService(Service[ProducedCommand]):
  def __init__(self):
    super().__init__(self)
    self.mediator = cast(type[MediatorProtocol], None)

  async def start(self) -> None:
    print("ReceiverService started.")
    self._is_running = True

  async def stop(self) -> None:
    print("ReceiverService stopped.")
    self._is_running = False

  async def handle(self, message, *, tx_context: TransactionContext, **_) -> None:
    print(f"Received message: {type(message).__name__} {message.number}")
    conn = await tx_context.connection
    result = await conn.fetch("SELECT 1;")
    await asyncio.sleep(10)
    print(result)


class ErrorRaisingService(Service):
  def __init__(self):
    super().__init__(self)

  async def start(self) -> None:
    print("ErrorRaisingService started.")
    # raise Exception("ErrorRaisingService error")
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

  app = MyApplication(
    configuration=configuration, database_dsn="postgresql://postgres:postgres@localhost:5432/postgres", logger=logger
  )
  app.register_service(server)
  app.register_service(ProducerService())
  app.register_service(ReceiverService())
  app.register_service(ErrorRaisingService())
  await app.start()


if __name__ == "__main__":
  asyncio.run(main())
