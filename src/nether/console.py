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
  logger.setLevel(max(logging.DEBUG, logging.WARNING - verbose * 10))
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


TRUE_VALUES = {"true", "1", "yes", "on"}


def parse_bool_env(env_value: str | int | None) -> bool:
  if env_value is None:
    return False
  elif isinstance(env_value, str):
    return env_value.lower().strip() in TRUE_VALUES
  else:
    return bool(env_value)


def postgres_string_from_credentials(
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


def postgres_string_from_env(env: dict[str, str], *, prefix: str = "", logger: logging.Logger | None = None) -> str:
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
  readonly = parse_bool_env(env.get(prefix + "READONLY"))
  return postgres_string_from_credentials(
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
