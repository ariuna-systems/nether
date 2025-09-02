"""
TODO This module implements a long running or CPU intensive process.
"""

from . import Component


class ProcessingComponent(Component):
    def __init__(self, application, *_, logger=None, **__):
        super().__init__(application, logger=logger, **__)

    async def on_start(self):
        return await super().on_start()

    async def on_stop(self):
        return await super().on_stop()

    def execute(self) -> None: ...
