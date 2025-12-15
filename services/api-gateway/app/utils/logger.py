from typing import Any
import logging
import inspect


def _get_caller_logger() -> logging.Logger:
    """
    Magic function to get the logger for the file that CALLED the function.
    This ensures logs show 'apps.monitors.view' instead of 'utils.logger'.
    """
    try:
        caller_frame = inspect.stack()[2]
        module_name = caller_frame[0].f_globals.get("__name__", "root")
        return logging.getLogger(module_name)
    except Exception:
        return logging.getLogger("api_gateway")


def log_info(message: str, **kwargs: Any) -> None:
    logger = _get_caller_logger()
    if kwargs:
        message = f"{message} | Context: {kwargs}"
    logger.info(message)


def log_warning(message: str, **kwargs: Any) -> None:
    logger = _get_caller_logger()
    if kwargs:
        message = f"{message} | Context: {kwargs}"
    logger.warning(message)


def log_error(message: str, exc_info: bool = False, **kwargs: Any) -> None:
    logger = _get_caller_logger()
    if kwargs:
        message = f"{message} | Context: {kwargs}"
    logger.error(message, exc_info=exc_info)


def log_debug(message: str, **kwargs: Any) -> None:
    logger = _get_caller_logger()
    if kwargs:
        message = f"{message} | Context: {kwargs}"
    logger.debug(message)
