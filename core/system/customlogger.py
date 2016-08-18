#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of EasyExp
#
# Copyright (C) 2016 Florian Perdreau, Radboud University Nijmegen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging


class CustomLogger(object):
    """
    CustomLogger class
    Wrapper class for built-in logger

    Usage:
    >>> # Instantiate CustomLogger
    >>> mylogger = CustomLogger(__name__, 'log_file.log', 'debug')
    >>> # Output a message
    >>> mylogger.logger.debug('debug message')
    >>> mylogger.logger.info('info message')
    >>> mylogger.logger.warn('warn message')
    >>> mylogger.logger.error('error message')
    >>> mylogger.logger.critical('critical message')
    """

    default_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    allowed_level = ['debug', 'info', 'warning', 'critical', 'fatal']

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
            format_str = CustomLogger.default_format

        self._name = name
        self._file_name = file_name

        # Set verbose level
        self._set_level(level)

        # Set logger
        self.logger = logging.getLogger(self._name)

        # Set output format
        formatter = logging.Formatter(format_str)

        # create console handler and set level to debug
        self.__ch = logging.StreamHandler()
        self.__ch.setLevel(self._level)
        self.__ch.setFormatter(formatter)

        # Set handler and output format
        self._handler = logging.FileHandler(self._file_name)
        self._handler.setFormatter(formatter)
        self.logger.setLevel(self._level)
        self._handler.setLevel(self._level)

        # Add handler to logger
        self.logger.addHandler(self._handler)

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
        if level not in CustomLogger.allowed_level:
            raise AttributeError('"{}" is not a valid verbose level. '
                                 'Possible options are debug, info, warning, critical or fatal'.format(level))
        if level == 'debug':
            self._level = logging.DEBUG
        elif level == 'info':
            self._level = logging.INFO
        elif level == 'warning':
            self._level = logging.WARNING
        elif level == 'critical':
            self._level = logging.CRITICAL
        elif level == 'fatal':
            self._level = logging.FATAL
