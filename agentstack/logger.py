import sys
import logging


def get_logger(name, debug=False):
    """
    Configure and get a logger with the given name.
    """
    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    formatter = logging.Formatter("%(asctime)s - %(process)d - %(threadName)s - %(filename)s:%(lineno)d - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger


log = get_logger(__name__)
