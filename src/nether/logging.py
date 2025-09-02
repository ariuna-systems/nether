import datetime
import logging
import sys

__all__ = ["configure_logger"]


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
