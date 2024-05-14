import logging


class CustomFormatter(logging.Formatter):
    """Кастомный форматер для логера."""

    green = '\x1b[32m'
    red = '\x1b[31m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'

    format = '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'

    FORMATS = {
        logging.DEBUG: green + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
