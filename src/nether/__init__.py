from abc import abstractmethod
import asyncio
import logging
import pprint
import sys
import threading
import traceback
from typing import Self
from typing import Protocol
import uuid

import concurrent

__version__ = "0.1.0"


class Runnable(Protocol):
    @abstractmethod
    def run() -> None: ...


class Stoppable(Protocol):
    @abstractmethod
    def stop() -> None: ...


def _loop_exception_handler(loop, context):
    """
    This is an logging exception handler for asyncio.
    It's purpose is to nicely log any unhandled excpetion that arises in the asyncio tasks.
    """

    exception = context.pop("exception", None)

    message = context.pop("message", "")
    if len(message) > 0:
        message += "\n"
    if len(context) > 0:
        message += pprint.pformat(context)

    if exception is not None:
        ex_traceback = exception.__traceback__
        tb_lines = [
            line.rstrip("\n")
            for line in traceback.format_exception(
                exception.__class__, exception, ex_traceback
            )
        ]
        message += f"'\n'{'\n'.join(tb_lines)}"

    logging.getLogger().error(message)


class Dispatcher:
    """
    Publish/Subscribe
    """

    def __init__(self) -> None: ...
    def register_subscriber(self, message_type, subscriber): ...
    def publish() -> None: ...  # notify/deliver


class Application:
    """
    NETHER application singleton instance.
    """

    def __init__(self, settings: None) -> None:
        self._services = {}
        self._settings = settings
        self._dispatcher = Dispatcher()

        try:
            self._event_loop = asyncio.get_running_loop()
        except RuntimeError:
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)

        self._event_loop.set_exception_handler(_loop_exception_handler)
        self._stop_event = asyncio.Event()
        self._stop_event.clear()

        self.event_queue = ...

        # TODO logging
        # TODO platform

    @property
    def services(self) -> None:
        return self._services

    def register_service(self, *services: Runnable) -> None:
        for service in services:
            if service.id not in self._services:
                self.services[service.id] = service

    def unregister_service(self, service_id: uuid.UUID) -> None:
        if service_id in self.services:
            del self.services[service_id]

    def start(self) -> None:
        self._event_loop.run_until_complete(asyncio.gather(self.main()))

    def restart(self) -> None: ...

    def stop(self) -> None:
        self._stop_event.set()
        print("stoped")

    def _before_start(self) -> None: ...

    def _before_stop(self) -> None: ...

    @abstractmethod
    async def main(self) -> None: ...


class Service(Runnable):
    def __init__(
        self, id: uuid.UUID, application: Application, description: str = None
    ) -> None:
        self.id = id
        self.name = type(self).__name__
        self.application = application
        self.description = description

    @classmethod
    async def create(cls, id, name, description) -> Self:
        cls(id, name, description)

    def __eq__(self, other: Self) -> bool:
        return self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))


class ServiceExample(Service):
    def __init__(self, id, application) -> None:
        super().__init__(id, application)

    async def run(self) -> None:
        print("service example")


def task(n):
    result = n
    for i in range(0, 10):
        result = result + i
    print(
        f"Task executed {threading.current_thread()}, result: {result}", file=sys.stderr
    )
    return result


class Example_Application_1(Application):
    def __init__(self, settings=None) -> None:
        super().__init__(settings=settings)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

    async def main(self) -> None:
        tasks = [
            self._event_loop.run_in_executor(self.executor, task, i)
            for i in range(100_000_000)
        ]
        results = await asyncio.gather(*tasks)
        print("Result:", sum(results))
        self.stop()


class Example_Application_2(Application):
    def __init__(self, settings=None) -> None:
        super().__init__(settings=settings)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

    async def main(self) -> None:
        # tasks = [
        #     self._event_loop.run_in_executor(self.executor, service.run)
        #     for service in self.services.values()
        # ]
        print("ex 2")
        # print(tasks)
        # results = await asyncio.gather(*tasks)


def main() -> None:
    # application = Example_Application_1(None)
    # application.register_service(ServiceExample(1, application))
    # application.start()

    application = Example_Application_2(None)
    application.register_service(ServiceExample(1, application))
    application.start()


if __name__ == "__main__":
    main()
