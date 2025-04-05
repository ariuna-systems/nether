import argparse
import logging
import os
import sys
from pathlib import Path

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


def configure_logger(logger: logging.Logger, verbose: int) -> None:
  logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S.%f %z"
  )
  logger.setLevel(logging.INFO if verbose == 0 else max(logging.DEBUG, logging.WARNING - verbose * 10))
  handler = logging.StreamHandler(stream=sys.stdout)
  handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S.%f %z")
  )
  logger.addHandler(handler)


def get_env(
  env_file: Path, mandatory_variables: list[str], optional_variables: list[str], *, logger: logging.Logger | None = None
) -> dict[str, str]:
  dotenv.load_dotenv(env_file)
  env: dict[str, str] = {}
  missing = []
  for env_var in mandatory_variables:
    if env_var not in os.environ:
      missing.append(env_var)
      if logger is not None:
        logger.error(f"Missing environment variable `{env_var}`.")
      else:
        print(f"Missing environment variable `{env_var}`.", file=sys.stderr)
    else:
      env[env_var] = os.environ[env_var].strip('"')
  for env_var in optional_variables:
    if env_var in os.environ:
      env[env_var] = os.environ[env_var].strip('"')
  if 0 < len(missing):
    sys.exit(1)

  return env
