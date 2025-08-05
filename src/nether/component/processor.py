"""
TODO This module implements a long running or CPU intensive process.
"""

from . import Component


class ProcessingComponent(Component):
  def __init__(self, application, *_, logger=None, **__):
    super().__init__(application, logger=logger, **__)

  def on_start(self):
    return super().start()

  def on_stop(self):
    return super().stop()

  def execute(self) -> None: ...
