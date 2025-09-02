import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import nether
from nether.component import Component
from nether.message import Command, Event, Message
from nether.server import Server


class System(nether.Nether):
  async def main(self) -> None:
    print("Started")


@dataclass(frozen=True, slots=True, kw_only=True)
class StopProducer(Command): ...


@dataclass(frozen=True, slots=True, kw_only=True)
class ProducerStopped(Event): ...


@dataclass(frozen=True, slots=True, kw_only=True)
class Result(Event):
  value: int


class Producer(Component[StopProducer]):
  """
  Producer sends a message to mediator until it receives stop event.
  """

  def __init__(self, application: System):
    super().__init__(application)
    self._value = 0
    self._finish = False
    self._task: asyncio.Task | None = None

  async def main(self):
    while not self._finish:
      event = Result(value=self._value)
      self._value += 1
      async with self.application.mediator.context() as ctx:
        await ctx.process(event)
        if self._finish:
          break
      print(f"Produced {event.value}")
      await asyncio.sleep(0.1)
      if self._finish:
        break

  async def on_start(self) -> None:
    self._finish = False
    self._task = asyncio.create_task(self.main())
    await super().on_start()
    self._logger.info("Started")

  async def on_stop(self) -> None:
    self._finish = True
    if self._task:
      await self._task
      self._task = None
    await super().on_stop()
    print(f"{self.__class__.__name__} stopped.")

  async def on_error(self) -> None: ...

  async def handle(
    self,
    message: StopProducer,
    *,
    handler: Callable[[Message], Awaitable[None]],
    channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
  ) -> None:
    self._finish = True


class Consumer(Component[Result]):
  def __init__(self, system: System, name: str | None = None):
    super().__init__(system)
    self.name = str(type(self)) if name is None else name

  async def on_start(self) -> None:
    print(f"{self.name} started")
    await super().on_start()

  async def on_stop(self) -> None:
    print(f"{self.name} stopped")
    await super().on_stop()

  async def handle(
    self,
    message: Result,
    *,
    handler: Callable[[Message], Awaitable[None]],
    channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
  ) -> None:
    print(f"{self.name} consumed {message.value}")
    # Only one consumer needs to send StopProducer, but all will receive events.
    if message.value >= 5 and self.name == "Consumer-1":
      await handler(StopProducer())


async def main():
  # single-producer/multi-consumer

  system = System(configuration={})
  system.attach(Producer(system))
  system.attach(Consumer(system, name="Consumer-1"))
  system.attach(Consumer(system, name="Consumer-2"))

  @dataclass(frozen=True, slots=True, kw_only=True)
  class ServerConfig:
    port: int = 8081
    host: str = "localhost"

  system.attach(Server(system, configuration=ServerConfig()))

  await system.start()


if __name__ == "__main__":
  try:
    nether.execute(main())
  except KeyboardInterrupt:
    print("Shutting down gracefully")
