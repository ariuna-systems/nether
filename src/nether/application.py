import asyncio
import concurrent
import logging
import platform
import pprint
import traceback
import uuid
from abc import abstractmethod

if platform.system() == "Windows":
    import win32api

from .common import Runnable
from .dispatcher import Dispatcher


class Application:
    """
    Represnt an application singleton instance.
    """

    def __init__(self, settings=None, *services) -> None:
        self._settings = settings
        self._mediator = Dispatcher()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        self._services = {}
        self._tasks = []

        for service in services:
            self.register_service(service)

        # Create asynchronous event loop.
        self._event_loop = asyncio.get_event_loop()
        if self._event_loop.is_closed():
            self._event_loop = asyncio.get_event_loop()
            asyncio.set_event_loop = self._event_loop

        # Configure asynchronous event loop.
        self._event_loop.set_exception_handler(self._loop_exception_handler)
        self._event_loop.set_debug(True)  # TODO: configurable

        # Handle interrupt events.
        if self.platform == "Windows":

            def handler(type):
                self.stop()
                return True

            win32api.SetConsoleCtrlHandler(handler, True)
        else:
            pass  # TODO POSIX/UNIX

        self._stop_event = asyncio.Event()
        self._stop_event.clear()
        self._stop_counter = 0
        self.event_queue = ...

        # TODO logging
        # TODO platform

    def _loop_exception_handler(loop, context):
        """
        This is an logging exception handler for asyncio tolog unhandled exception that arises in the asyncio tasks.
        """
        exception = context.pop("exception", None)
        print(exception)
        # message = context.pop("message", "")
        # if len(message) > 0:
        #     message += "\n"
        # if len(context) > 0:
        #     message += pprint.pformat(context)

        # if exception is not None:
        #     ex_traceback = exception.__traceback__
        #     tb_lines = [
        #         line.rstrip("\n")
        #         for line in traceback.format_exception(
        #             exception.__class__, exception, ex_traceback
        #         )
        #     ]
        #     message += f"'\n'{'\n'.join(tb_lines)}"

        # logging.error(message)

    @property
    def platform(self) -> str | None:
        """Return OS platfrom name e.g. Windows, Linux etc.
        None means unrecognized.
        """
        system = platform.system()
        return None if system == "" else system

    @property
    def services(self) -> None:
        """Get the registered service."""
        return self._services

    def register_service(self, *services: Runnable) -> None:
        for service in services:
            if service.id not in self._services:
                service.application = self
                self.services[service.id] = service

    def unregister_service(self, service_id: uuid.UUID) -> None:
        if service_id in self.services:
            del self.services[service_id]

    def start(self) -> None:
        try:
            self._stop_event.clear()
            self._event_loop.run_until_complete(asyncio.gather(self.main()))
            self._event_loop.run_until_complete(self._event_loop.shutdown_asyncgens())
            self._event_loop.close()
        finally:
            logging.info("[FINISHED]")

        # try:
        #     self._event_loop = asyncio.get_running_loop()
        # except RuntimeError:
        #     self._event_loop = asyncio.new_event_loop()
        #     asyncio.set_event_loop(self._event_loop)
        # self._stop_event = asyncio.Event()
        # self._stop_event.clear()

    def restart(self) -> None:
        logging.info("restart")

    def stop(self) -> None:
        self._stop_event.set()
        # print(self._event_loop.all_tasks())
        print("stop")

    def _before_start(self) -> None:
        logging.info("before start")

    def _before_stop(self) -> None:
        logging.info("after start")

    @abstractmethod
    async def main(self) -> None:
        """Must be implemented in your application."""
        raise NotImplementedError
