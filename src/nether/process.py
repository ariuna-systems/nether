import asyncio
from nether.service import Service


class ProcessService(Service):
    """
    Service to manage background processes running on the application event loop.

    * coroutine
    * asyncio.Future
    * asyncio.Task
    """

    def __init__(self, application=None) -> None:
        super().__init__(
            id="nether.ProcessService",
            description="backgroun processing",
            application=application,
        )
        self._worker = None
        self._waiting_tasks = asyncio.Queue()
        self._pending_tasks = set()

    async def main(self) -> None:
        while True:
            print(self, "running")

    async def start(self) -> None:
        self._worker = asyncio.ensure_future(self.main())
        self._worker.add_done_callback(self._on_task_exit)

    def _on_task_exit(self) -> None:
        if self._worker is None:
            return
        try:
            self._worker.result()
        except asyncio.CancelledError:
            pass
        except Exception as error:
            print(f"Error '{error}' during task service:")
        self._worker = None
        print("Main task exited unexpectedly, restarting...")
        self.start()

    async def before_start() -> None: ...
    async def before_leave() -> None: ...
