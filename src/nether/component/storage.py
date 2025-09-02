from . import Component


class StorageComponent(Component):
  def __init__(self, application, *_, **__) -> None:
    super().__init__(application)
