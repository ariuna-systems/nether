import datetime
import logging
import sys
from pathlib import Path

__all__ = ["configure_global_logging", "configure_logger"]


class DatetimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):  # noqa: N802
        dt = datetime.datetime.fromtimestamp(record.created).astimezone()
        base_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        milliseconds = f"{dt.microsecond // 1000:03d}"
        offset = dt.strftime("%z")
        formatted_offset = f"{offset[:3]}:{offset[3:]}"
        return f"{base_time}.{milliseconds} {formatted_offset}"


def configure_logger(logger: logging.Logger, verbose: int = 0) -> None:
    """Configure a specific logger with basic stdout logging (legacy function)."""
    logger.setLevel(max(logging.DEBUG, logging.WARNING - verbose * 10))
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = DatetimeFormatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", style="%")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def configure_global_logging(log_level: str = "INFO", log_file: Path | None = None, verbose: int = 0) -> None:
    """Configure global logging with both stdout and optional file logging."""
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Adjust level based on verbose flag
    if verbose > 0:
        numeric_level = max(logging.DEBUG, numeric_level - verbose * 10)

    # Create formatter
    formatter = DatetimeFormatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", style="%")

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Add stdout handler
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(numeric_level)
    root_logger.addHandler(stdout_handler)

    # Add file handler if log_file is specified
    if log_file is not None:
        try:
            # Ensure parent directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Create file handler
            file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(numeric_level)
            root_logger.addHandler(file_handler)

            root_logger.info(f"File logging enabled: {log_file}")
        except Exception as e:
            root_logger.error(f"Failed to setup file logging to {log_file}: {e}")

    # Configure specific loggers to not propagate to avoid duplicate logs
    # if they were already configured with the old configure_logger function
    for name in ["nether.mediator", "nether.system"]:
        logger = logging.getLogger(name)
        logger.propagate = True  # Let them propagate to root
        # Clear their individual handlers to avoid duplicates
        logger.handlers.clear()
