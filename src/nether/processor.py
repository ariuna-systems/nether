from .extension import Service


class ProcessingService(Service):
  def __init__(self, application, *_, logger=None, **__):
    super().__init__(application, logger=logger, **__)

  def on_start(self):
    return super().start()

  def on_stop(self):
    return super().stop()
