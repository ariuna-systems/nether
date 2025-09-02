"""
Service discovery mechanisms.
"""

from . import Component


class DiscoveryComponent(Component):
  def __init__(self, application, *_, **__) -> None:
    super().__init__(application)
