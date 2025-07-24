"""
Configuration for application or service.
"""

from typing import Self


class Configuration:  # TODO
  """
  Configuration for application or service.
  """

  def __init__(self, *_, **__) -> None: ...

  def __str__(self) -> str: ...

  @staticmethod
  def load(self, source: str) -> Self:
    return type(self)()
