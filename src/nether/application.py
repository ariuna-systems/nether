import argparse
import asyncio
import logging
import platform
import signal
import sys
import traceback
from abc import abstractmethod
from typing import Any

from .console import configure_logger
from .mediator import (
  Mediator,
  MediatorProtocol,
)
from .service import ServiceProtocol
from .transaction import TransactionManager

local_logger = logging.getLogger(__name__)
local_logger.propagate = False
configure_logger(local_logger, 1)


def run_main(coroutine):
  if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
  asyncio.run(coroutine)


class Application:
  """Represent an application singleton instance."""

  def __init__(
    self,
    *,
    mediator: MediatorProtocol = Mediator(),  # noqa: B008
    configuration: argparse.Namespace,
    database_dsn: str,
    logger: logging.Logger = local_logger,
  ) -> None:
    self.configuration = configuration
    self._mediator = mediator
    self._stop_event = asyncio.Event()
    self.logger = logger
    self._database_dsn = database_dsn
    self._transaction_manager = TransactionManager(
      logger=logger, dsn=self._database_dsn, min_pool_size=0, max_pool_size=10
    )
    self._services: set[ServiceProtocol] = set()

    # TODO: uptime, background processing

  @property
  def platform(self) -> str | None:
    """Return a platform name (e.g. Windows, Linux) or None if unrecognized."""
    platform_name = platform.system()
    return None if platform_name == "" else platform_name

  @property
  def transaction_manager(self) -> TransactionManager:
    return self._transaction_manager

  @property
  def mediator(self) -> MediatorProtocol:
    """Get the mediator instance."""
    return self._mediator

  @property
  def services(self) -> set[ServiceProtocol[Any]]:
    """Get the registered service."""
    return self._services

  async def _setup_components(self) -> None:
    self._mediator.set_application(self)
    await self._transaction_manager.initialize()

  def register_service(self, *services: ServiceProtocol[Any]) -> None:
    for service in services:
      if service not in self.services:
        service.set_application(self)
        self._services.add(service)  # TODO: Udržovat služby na aplikaci a předat mediatoru instanci aplikace

  def unregister_service(self, *services: ServiceProtocol[Any]) -> None:
    for service in services:
      if service in self.services:
        self._services.remove(service)

  def _setup_signal_handlers(self) -> None:
    """Setup handlers for interrupt signals"""

    def set_stop(*args):
      self._stop_event.set()
      self.logger.info("Shutdown signal set.")

    signal.signal(signal.SIGINT, set_stop)
    signal.signal(signal.SIGTERM, set_stop)

  async def start(self) -> None:
    try:
      await self._before_start()
      await self.main()

      while not self._stop_event.is_set() and any(service.is_running for service in self.services):
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
    for service in self.services:
      try:
        await service.stop()
      except Exception as error:
        self.logger.debug(f"Traceback for error below: {traceback.format_exc()}")
        self.logger.error(f"Error stopping a service `{type(service).__name__}`: {error}")
    self.logger.info("stop")

  async def _before_start(self) -> None:
    self._setup_signal_handlers()
    await self._setup_components()
    for service in self.services:
      try:
        await service.start()
        self.logger.info(f"Service `{type(service).__name__}` started.")
      except Exception as error:
        self.logger.debug(f"Traceback for error below: {traceback.format_exc()}")
        self.logger.error(f"Error starting a service `{type(service).__name__}`: {error}")
        sys.exit(1)

  @abstractmethod
  async def main(self) -> None:
    """Must be implemented in your application."""
    raise NotImplementedError
