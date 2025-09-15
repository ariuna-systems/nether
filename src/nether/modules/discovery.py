"""
Service discovery mechanisms.
"""

from . import Module


class DiscoveryComponent(Module):
    def __init__(self, application, *_, **__) -> None:
        super().__init__(application)
