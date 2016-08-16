#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Florian Perdreau (f.perdreau@donders.ru.nl)

import logging


class CustomLogger(object):
    """
    CustomLogger class
    Wrapper class for built-in logger

    Usage:
    >>> # Instantiate CustomLogger
    >>> mylogger = CustomLogger('root', 'log_file.log', 'info')
    >>> # Output a message
    >>> mylogger.logger.info('Hello, world!')

    """

    default_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    def __init__(self, name='', file_name='log.txt', level='debug', format_str=None):
        """
        CustomLogger constructor

        Parameters
        ----------
        :param name: logger name
        :param file_name: full path to handler (e.g. file_name = 'some/path/to/log_file.log')
        :param level: verbose level
        :param format_str: output format
        """

        if format_str is None:
            self._formatter = CustomLogger.default_format

        self._name = name
        self._file_name = file_name

        # Set output format
        self._handler.setFormatter(logging.Formatter(format_str))

        # Set verbose level
        self._set_level(level)
        self.logger.setLevel(self._level)
        self._handler.setLevel(self._level)

        # Add handler to logger
        self.logger.addHandler(self._handler)

    @property
    def _handler(self):
        return logging.FileHandler(self._file_name)

    @property
    def logger(self):
        return logging.getLogger(self._name)

    def _set_level(self, level):
        """
        Set verbose level
        Parameters
        ----------
        level: str
            verbose level (debug, info or warning)
        Returns
        -------

        """
        if level == 'debug':
            self._level = logging.DEBUG
        elif level == 'info':
            self._level = logging.INFO
        elif level == 'warning':
            self._level = logging.WARNING