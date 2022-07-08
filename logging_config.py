import enum
import logging
import os


class Colors(str, enum.Enum):
    grey = "\x1b[0;37m"
    green = "\x1b[1;32m"
    yellow = "\x1b[1;33m"
    red = "\x1b[1;31m"
    bold_red = "\x1b[31;1m"
    purple = "\x1b[1;35m"
    blue = "\x1b[1;34m"
    light_blue = "\x1b[1;36m"
    reset = "\x1b[0m"
    blink_red = "\x1b[5m\x1b[1;31m"


class CustomFormatter(logging.Formatter):
    format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    )

    FORMATS = {
        logging.DEBUG: Colors.green + format + Colors.reset,
        logging.INFO: Colors.green + format + Colors.reset,
        logging.WARNING: Colors.yellow + format + Colors.reset,
        logging.ERROR: Colors.red + format + Colors.reset,
        logging.CRITICAL: Colors.bold_red + format + Colors.reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def get_logger(name: str) -> logging.Logger:
    handler = logging.StreamHandler()
    formatter = CustomFormatter()
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
    root.addHandler(handler)

    return logging.getLogger(name)
