import argparse
import asyncio
import random
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from nether import Application, execute
from nether.component import Component
from nether.message import Command, Event, Message
from nether.server import Server


class Showcase(Application):
  async def main(self) -> None:
    print("Hello, world!")


@dataclass(frozen=True, slots=True, kw_only=True)
class Intent(Command):
  value: int = 0


@dataclass(frozen=True, slots=True, kw_only=True)
class Result(Event):
  value: int = 0


class Producer(Component[Intent]):
  def __init__(self, application: Application):
    super().__init__(application)
    print(f"Producer supports: {self.supports}")
    self.running_thread: threading.Thread | None = None
    self._stop_event = threading.Event()

  async def _produce_command(self, command: Command) -> None:
    if self.application:
      async with self.application.mediator.context() as ctx:
        await ctx.process(command)

  def _worker(self):
    """Worker function that runs in a separate thread."""
    number = 0
    while not self._stop_event.is_set():
      number += 1
      command = Intent(value=number)
      print(f"Produced message: {type(command).__name__} {command.value}")
      # Create new event loop for this thread
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      try:
        loop.run_until_complete(self._produce_command(command))
      finally:
        loop.close()
      time.sleep(0.5)

  async def on_start(self) -> None:
    self._logger.info(f"{self.__class__.__name__} started.")
    self._stop_event.clear()
    self.running_thread = threading.Thread(target=self._worker)
    self.running_thread.daemon = True  # Thread will stop when main program exits
    self.running_thread.start()
    await super().on_start()

  async def on_stop(self) -> None:
    self._logger.info(f"{self.__class__.__name__} stopped.")
    if self.running_thread:
      self._stop_event.set()
      self.running_thread.join(timeout=2.0)  # Wait max 2 seconds
      self.running_thread = None
    await super().on_stop()
    print("Producer stopped.")

  async def handle(
    self,
    message: Intent,
    *,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
  ) -> None:
    # When we receive a Intent command, dispatch a Result event.
    print(f"Producer handling: {type(message).__name__} {message.value}")
    produced_event = Result(value=message.value)
    print(f"Producer dispatching: {type(produced_event).__name__} {produced_event.value}")
    await dispatch(produced_event)


class Consumer(Component[Result]):
  def __init__(self, application: Application):
    super().__init__(application)
    print(f"Consumer supports: {self.supports}")

  async def on_start(self) -> None:
    self._logger.info(f"{self.__class__.__name__} started.")
    await super().on_start()

  async def on_stop(self) -> None:
    self._logger.info(f"{self.__class__.__name__} stopped.")
    await super().on_stop()

  async def handle(
    self,
    message: Result,
    *,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
  ) -> None:
    print(f"Consumed: {type(message).__name__} {message.value}")
    await asyncio.sleep(random.randint(1, 4))
    # You can add more logic here to react to the produced message.
    # For example, you could dispatch another event or perform some processing.


async def main():
  configuration = argparse.Namespace()
  configuration.host = "localhost"
  configuration.port = 8081
  showcase = Showcase(configuration=configuration)

  showcase.register_module(Producer(showcase))
  showcase.register_module(Consumer(showcase))
  showcase.register_module(Server(showcase, configuration=configuration))

  await showcase.start()


if __name__ == "__main__":
  try:
    execute(main())
  except KeyboardInterrupt:
    print("Shutting down gracefully...")
