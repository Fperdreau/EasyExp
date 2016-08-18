#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of EasyExp
#
# Copyright (C) 2015 Florian Perdreau, Radboud University Nijmegen
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

import time

"""
This file is for Timer class
"""


class Timer(object):
    """
    Timer class
    Implements a simple timer with start, stop and reset methods. Timer can works as a timer (returns elapsed time) or
    as a countdown (if max_duration is specified)

    Usage:
    >>> # Example:
    >>> timer = Timer()
    >>> # Then, to start the timer
    >>> timer.start()
    >>> # Stop the timer
    >>> time.sleep(2.0)
    >>> timer.stop()
    >>> # Get elapsed time
    >>> print(timer.get_time('elapsed'))
    2.0
    >>> # Reset timer
    >>> timer.reset()
    """

    def __init__(self, max_duration=None):
        """
        Timer constructor
        :param max_duration: max duration of timer (in seconds). If not None, then timer will work backward
        (max_duration => 0)
        :type max_duration: float
        """
        self.__start_time = None
        self.__stop_time = None
        self.__max_duration = max_duration

    @property
    def elapsed(self):
        if self.__start_time is not None:
            return (time.time() - self.__start_time)

    @property
    def countdown(self):
        if self.__start_time is not None and self.__max_duration is not None:
            elapsed = (self.__max_duration - (time.time() - self.__start_time))
            return 0.0 if elapsed <= 0.0 else elapsed

    def start(self):
        """
        Starts timer
        """
        if self.__start_time is None:
            self.__start_time = time.time()

    def stop(self):
        """
        Stops timer
        """
        self.__stop_time = self.elapsed

    def reset(self):
        """
        Resets timer
        """
        self.__start_time = None

    def get_time(self, prop):
        """
        Time getter

        Parameters
        ----------
        prop: property name (start, stop or elapsed)

        Returns
        -------
        :rtype: float
        """
        if prop is 'start':
            return self.__start_time
        elif prop is 'stop':
            return self.__stop_time
        elif prop is 'elapsed':
            return self.elapsed
        else:
            raise AttributeError('{} property does not exist')

if __name__ == '__main__':
    # Countdown
    max_duration = 2000
    timer = Timer(max_duration=max_duration)
    timer.start()
    print(timer.countdown)
    while timer.countdown > 0.0:
        print(timer.countdown)
    timer.stop()
    timer.reset()
