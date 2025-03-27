import argparse
import asyncio
import logging
import platform
import signal
import sys
from abc import abstractmethod
from typing import Any

from .mediator import (
  Mediator,
  MediatorProtocol,
  ServiceProtocol,
)

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
    mediator: MediatorProtocol = Mediator(),  # noqa: B008
    configuration: argparse.Namespace,
    logger: logging.Logger = local_logger,
  ) -> None:
    self.configuration = configuration
    self._mediator = mediator
    self.logger = logger
    self._stop_event = asyncio.Event()

  @property
  def platform(self) -> str | None:
    """Return OS platform name e.g. Windows, Linux etc.
    None means unrecognized.
    """
    system = platform.system()
    return None if system == "" else system

  @property
  def mediator(self) -> MediatorProtocol:
    """Get the mediator instance."""
    return self._mediator

  @property
  def services(self) -> set[ServiceProtocol[Any]]:
    """Get the registered service."""
    return self._mediator.services

  def register_service(self, *services: ServiceProtocol[Any]) -> None:
    for service in services:
      if service not in self._mediator.services:
        service.set_application(self)
        self._mediator.register(service)  # TODO: Možná udržovat služby na aplikaci a předat mediatoru instanci aplikace

  def unregister_service(self, *services: ServiceProtocol[Any]) -> None:
    for service in services:
      if service in self._mediator.services:
        self._mediator.unregister(service)

  def _setup_signal_handlers(self) -> None:
    """Setup handlers for interrupt signals"""

    def set_stop(*args):
      self._stop_event.set()
      self.loogger.info("Shutdown signal set.")

    signal.signal(signal.SIGINT, set_stop)
    signal.signal(signal.SIGTERM, set_stop)

  async def start(self) -> None:
    try:
      self._setup_signal_handlers()
      await self._before_start()
      await self.main()

      while not self._stop_event.is_set() and any(service.is_running for service in self._mediator.services):
        await asyncio.sleep(0.5)
    except asyncio.CancelledError:
      self.logger.info("Application cancelled")
    except Exception as e:
      self.logger.error(f"Application error: {e}")
      raise
    finally:
      await self.stop()
      self.logger.info("[FINISHED]")

  async def stop(self) -> None:
    await self._mediator.stop()
    self.logger.info("stop")

  async def _before_start(self) -> None:
    for service in self.services:
      try:
        await service.start()
        self.logger.info(f"Service `{type(service).__name__}` started.")
      except Exception as error:
        self.logger.error(f"Error starting service `{type(service).__name__}`: {error}")
    self.logger.info("before start")

  @abstractmethod
  async def main(self) -> None:
    """Must be implemented in your application."""
    raise NotImplementedError
