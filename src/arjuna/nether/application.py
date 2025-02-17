import argparse
import asyncio
import logging
import platform
import sys
from abc import abstractmethod
from typing import Any

from .mediator import Mediator, MediatorProtocol, ServiceProtocol, UnitOfWork, UnitOfWorkProtocol

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
local_logger = logging.getLogger(__name__)
local_logger.propagate = False
handler = logging.StreamHandler(stream=sys.stdout)
local_logger.addHandler(handler)


class Application:
  """Represent an application singleton instance."""

  def __init__(
    self,
    *,
    mediator: type[MediatorProtocol] = Mediator,
    unit_of_work: type[UnitOfWorkProtocol] = UnitOfWork,
    configuration: argparse.Namespace,
    logger: logging.Logger = local_logger,
  ) -> None:
    self.configuration = configuration
    self._mediator = mediator
    self._unit_of_work = unit_of_work
    self.logger = logger

  @property
  def platform(self) -> str | None:
    """Return OS platform name e.g. Windows, Linux etc.
    None means unrecognized.
    """
    system = platform.system()
    return None if system == "" else system

  @property
  def services(self) -> set[ServiceProtocol[Any]]:
    """Get the registered service."""
    return self._mediator.services()

  def register_service(self, *services: ServiceProtocol[Any]) -> None:
    for service in services:
      if service not in self._mediator.services():
        self._mediator.register(service)

  def unregister_service(self, *services: ServiceProtocol[Any]) -> None:
    for service in services:
      if service in self._mediator.services():
        self._mediator.unregister(service)

  async def start(self) -> None:
    try:
      await self._before_start()
      await self.main()

      while any(service.is_running for service in self._mediator.services()):
        await asyncio.sleep(1)
    finally:
      self.logger.info("[FINISHED]")

  async def stop(self) -> None:
    await self._mediator.stop()
    self.logger.info("stop")

  async def _before_start(self) -> None:
    for service in self.services:
      await service.start()
    self.logger.info("before start")

  @abstractmethod
  async def main(self) -> None:
    """Must be implemented in your application."""
    raise NotImplementedError
