import argparse
import asyncio
import logging
import platform
import signal
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
    self._shutdown_event = asyncio.Event()

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

  async def _signal_handler(self) -> None:
    """Handle shutdown signals"""
    self.logger.info("Received shutdown signal, stopping services...")
    self._shutdown_event.set()

  def _setup_signal_handlers(self) -> None:
    """Setup handlers for interrupt signals"""
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
      loop.add_signal_handler(sig, lambda: asyncio.create_task(self._signal_handler()))

  async def start(self) -> None:
    try:
      self._setup_signal_handlers()
      await self._before_start()
      await self.main()

      while not self._shutdown_event.is_set() and any(service.is_running for service in self._mediator.services()):
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
      except Exception as error:
        self.logger.error(f"Error starting service {type(service).__name__}: {error}")
    self.logger.info("before start")

  @abstractmethod
  async def main(self) -> None:
    """Must be implemented in your application."""
    raise NotImplementedError
