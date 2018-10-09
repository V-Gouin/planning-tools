#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Documentation"""

import logging
from typing import List
import os

import click
from colorlog import ColoredFormatter

# Human logging levels
log_levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}
CLICKVERBOSITY = click.Choice(list(log_levels.keys()))


def set_logging_config(verbosity, filename=None):
    """A function to define the configuration of the logging module

    Args:
        verbosity (str):
            A valid verbosity level as defined in `log_levels`

        filename (Optional[str]):
            The filename to write the logs
    """
    if verbosity == 'debug':
        colored_fmt = '{log_color}{levelname}:{name}.{funcName}:{message}'
        file_fmt = '{levelname}:{name}.{funcName}:{message}'
    else:
        colored_fmt = '{log_color}{levelname}:{message}'
        file_fmt = '{levelname}:{message}'
    colored_formatter = ColoredFormatter(
        style='{',
        fmt=colored_fmt,
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'white',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )
    handler = logging.StreamHandler()
    handler.setFormatter(colored_formatter)
    handlers = [handler]  # type: List[logging.Handler]

    if filename is not None:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        handler = logging.FileHandler(filename=filename, mode='w')
        file_formatter = logging.Formatter(fmt=file_fmt, style='{')
        handler.setFormatter(file_formatter)
        handlers.append(handler)

    # Define the basic config
    logging.basicConfig(level=log_levels[verbosity], handlers=handlers)
