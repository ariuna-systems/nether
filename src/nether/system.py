import argparse
import asyncio
import logging
import os
import platform
import signal
import sys
import traceback
from abc import abstractmethod
from enum import StrEnum, unique
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import dotenv

from .component import Component
from .logging import configure_logger
from .mediator import Mediator

__all__ = ["Nether"]


local_logger = logging.getLogger(__name__)
local_logger.propagate = False

configure_logger(local_logger)


def _create_parser(
  *,
  prog: str,
  description: str,
  env_file: bool = False,
  verbose: bool = False,
  host: bool = False,
  port: bool = False,
  production: bool = False,
  version: str | None = None,
) -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(prog=prog, description=description)
  if env_file:
    parser.add_argument(
      "--env-file",
      type=Path,
      default=Path(".env"),
      help="Path to the environment file.",
    )
  if verbose:
    parser.add_argument(
      "--verbose",
      "-v",
      action="count",
      default=0,
      required=False,
      help="Increase the verbosity level.",
    )
  if host:
    parser.add_argument("--host", default="localhost", required=False, help="Set http server host.")
  if port:
    parser.add_argument("--port", default=8080, required=False, help="Set http server port.")
  if version is not None:
    parser.add_argument(
      "--version",
      action="version",
      version=f"%(prog)s {version}",
    )
  if production:
    parser.add_argument(
      "--production",
      dest="production",
      action="store_true",
      required=False,
      default=False,
      help="Run the production mode.",
    )

  return parser


def _get_env(
  env_file: Path,
  *,
  mandatory_variables: list[str] | None = None,
  optional_variables: list[str] | None = None,
  logger: logging.Logger | None = None,
) -> dict[str, str]:
  dotenv.load_dotenv(env_file)
  env: dict[str, str] = {}
  missing = []
  if mandatory_variables is not None:
    for env_var in mandatory_variables:
      if env_var not in os.environ:
        missing.append(env_var)
        if logger is not None:
          logger.error(f"Missing environment variable `{env_var}`.")
        else:
          print(f"Missing environment variable `{env_var}`.", file=sys.stderr)
      else:
        env[env_var] = os.environ[env_var].strip('"')
  if optional_variables is not None:
    for env_var in optional_variables:
      if env_var in os.environ:
        env[env_var] = os.environ[env_var].strip('"')
  if 0 < len(missing):
    sys.exit(1)

  return env


TRUE_VALUES = {"true", "1", "yes", "on"}


def _parse_bool_env(env_value: str | int | None) -> bool:
  if env_value is None:
    return False
  elif isinstance(env_value, str):
    return env_value.lower().strip() in TRUE_VALUES
  else:
    return bool(env_value)


def _postgres_string_from_credentials(
  *,
  host: str,
  port: str,
  dbname: str,
  schema: str | None = None,
  user: str,
  password: str,
  readonly: bool = False,
) -> str:
  connection_string = f"postgresql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{dbname}"
  options = []
  if schema is not None:
    options.append(f"search_path={schema}")
  if readonly:
    options.append("default_transaction_read_only=on")
  if options:
    options_value = " ".join([f"-c {opt}" for opt in options])
    connection_string += f"?options={quote_plus(options_value)}"

  return connection_string


def _postgres_string_from_env(env: dict[str, str], *, prefix: str = "", logger: logging.Logger | None = None) -> str:
  """
  Env has to contain {HOST, PORT, NAME, USER, PASSWORD} or DSN which overrides all other options.
  Env can contain SCHEMA, READONLY (bool).
  """
  if (dsn := env.get(prefix + "DSN")) is not None:
    if logger is not None and (prefix + "HOST") in env:  # If there are other options, log override
      logger.debug("Database DSN found, overriding other options.")

    return dsn

  host = env[prefix + "HOST"]
  port = env[prefix + "PORT"]
  dbname = env[prefix + "NAME"]
  schema = env.get(prefix + "SCHEMA")
  user = env[prefix + "USER"]
  password = env[prefix + "PASSWORD"]
  readonly = _parse_bool_env(env.get(prefix + "READONLY"))
  return _postgres_string_from_credentials(
    host=host, port=port, dbname=dbname, schema=schema, user=user, password=password, readonly=readonly
  )


def log_configuration(
  configuration: argparse.Namespace, *, logger: logging.Logger, level: int = logging.DEBUG, prefix: str = ""
) -> None:
  for argument_name, argument_value in sorted(vars(configuration).items()):
    full_name = f"{prefix}{argument_name}" if prefix else argument_name
    if isinstance(argument_value, argparse.Namespace):
      log_configuration(argument_value, logger=logger, level=level, prefix=f"{full_name}.")
    else:
      logger.log(level, f"{full_name}: {argument_value}")


def execute(coroutine):
  if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
  asyncio.run(coroutine)


class Nether:
  """Represent an application singleton instance."""

  @unique
  class State(StrEnum):
    STARTING = "starting"
    OPERATING = "operating"

  def __init__(
    self,
    *,
    mediator=Mediator(),  # noqa: B008
    configuration: argparse.Namespace,  # TODO Configuration class
    logger: logging.Logger = local_logger,
  ) -> None:
    self.configuration = configuration
    self._mediator = mediator
    self._stop_event = asyncio.Event()
    self.logger = logger
    self._services: set[Component] = set()

  @property
  def platform(self) -> str | None:
    """Return a platform name (e.g. Windows, Linux) or None if unrecognized."""
    platform_name = platform.system()
    return None if platform_name == "" else platform_name

  @property
  def mediator(self) -> Mediator:
    """Get the mediator instance."""
    return self._mediator

  @property
  def components(self) -> set[Component[Any]]:
    """Get the registered components."""
    return self._mediator.components

  def attach(self, *components: Component[Any]) -> None:
    for component in components:
      if component not in self._mediator.components:
        self._mediator.attach(component)

  def detach(self, *components: Component[Any]) -> None:
    for component in components:
      if component in self._mediator.components:
        self._mediator.detach(component)

  def _setup_signal_handlers(self) -> None:
    """Setup handlers for interrupt signals"""

    def set_stop(*args):
      self._stop_event.set()
      self.logger.info("Shutdown signal set.")

    signal.signal(signal.SIGINT, set_stop)
    signal.signal(signal.SIGTERM, set_stop)

  async def start(self) -> None:
    try:
      for component in self.components:
        try:
          await component.on_start()
          self.logger.info(f"component `{type(component).__name__}` started.")
        except Exception as error:
          self.logger.error(f"component `{type(component).__name__}` failed: {error}")
          sys.exit(1)
      await self.main()
      while not self._stop_event.is_set() and any(component.state for component in self._mediator.components):
        await asyncio.sleep(0.25)
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
    for component in self.components:
      try:
        await component.stop()
      except Exception as error:
        self.logger.debug(f"Traceback for error below: {traceback.format_exc()}")
        self.logger.error(f"Error stopping a service `{type(component).__name__}`: {error}")
    self.logger.info("stop")

  @abstractmethod
  async def main(self) -> None:
    """Must be implemented in your application."""
    raise NotImplementedError
