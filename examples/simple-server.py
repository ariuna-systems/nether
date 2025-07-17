import argparse
import asyncio
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

    # Start the HTTP server
    # async with self.mediator.context() as ctx:
    #   await ctx.process(StartServer(host="localhost", port=8080))


@dataclass(frozen=True, slots=True, kw_only=True)
class Produce(Command):
  value: int = 0


@dataclass(frozen=True, slots=True, kw_only=True)
class Produced(Event):  # Changed back to Event
  value: int = 0


class Producer(Component[Produce]):
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
      command = Produce(value=number)
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
    message: Produce,
    *,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
  ) -> None:
    # When we receive a Produce command, dispatch a Produced event
    print(f"Producer handling: {type(message).__name__} {message.value}")
    produced_event = Produced(value=message.value)
    print(f"Producer dispatching: {type(produced_event).__name__} {produced_event.value}")
    await dispatch(produced_event)


class Consumer(Component[Produced]):
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
    message: Produced,
    *,
    dispatch: Callable[[Message], Awaitable[None]],
    join_stream: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
  ) -> None:
    print(f"Consumed: {type(message).__name__} {message.value}")
    await asyncio.sleep(3)  # Simulate some processing time
    # You can add more logic here to react to the produced message.
    # For example, you could dispatch another event or perform some processing.


async def main():
  configuration = argparse.Namespace()
  configuration.host = "localhost"
  configuration.port = 8080
  showcase = Showcase(configuration=configuration)

  showcase.register_module(Producer(showcase))
  showcase.register_module(Consumer(showcase))
  showcase.register_module(Server(showcase, configuration=configuration))  # Commented out to avoid errors

  await showcase.start()


if __name__ == "__main__":
  execute(main())
