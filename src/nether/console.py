"""
This module contains command line interface related classes and functions.
"""

import argparse
import datetime
import logging
import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

import dotenv


def create_parser(
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


class DatetimeFormatter(logging.Formatter):
  def formatTime(self, record, datefmt=None):  # noqa: N802
    dt = datetime.datetime.fromtimestamp(record.created).astimezone()
    base_time = dt.strftime("%Y-%m-%d %H:%M:%S")
    milliseconds = f"{dt.microsecond // 1000:03d}"
    offset = dt.strftime("%z")
    formatted_offset = f"{offset[:3]}:{offset[3:]}"
    return f"{base_time}.{milliseconds} {formatted_offset}"


def configure_logger(logger: logging.Logger, verbose: int = 0) -> None:
  logger.setLevel(logging.INFO if verbose == 0 else max(logging.DEBUG, logging.WARNING - verbose * 10))
  handler = logging.StreamHandler(stream=sys.stdout)
  formatter = DatetimeFormatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", style="%")
  handler.setFormatter(formatter)
  logger.addHandler(handler)


def get_env(
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


def postgres_string_from_env(env: dict[str, str], *, prefix: str = "") -> str:
  host = env[prefix + "DATABASE_HOST"]
  port = env[prefix + "DATABASE_PORT"]
  dbname = env[prefix + "DATABASE_NAME"]
  schema = env.get(prefix + "DATABASE_SCHEMA")
  user = env[prefix + "DATABASE_USER"]
  password = env[prefix + "DATABASE_PASSWORD"]
  timeout = env[prefix + "DATABASE_TIMEOUT"]
  connection_string = (
    f"postgresql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{dbname}?connect_timeout={timeout}"
  )
  if schema is not None:
    connection_string += f"&options=-c%20search_path%3D{schema}"
  return connection_string


def log_configuration(configuration: argparse.Namespace, *, logger: logging.Logger, level: int = logging.DEBUG) -> None:
  for argument_name, argument_value in vars(configuration).items():
    logger.log(level, f"{argument_name}: {argument_value}")
