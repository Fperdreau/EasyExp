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
    >>># Example:
    >>>timer = Timer()
    >>>#  Then, to start the timer
    >>>timer.start()
    >>># Stop the timer
    >>>timer.stop()
    >>># Get elapsed time
    >>>timer.elapsed
    >>># Reset timer
    >>>timer.reset()
    """

    def __init__(self, max_duration=None):
        """
        Timer constructor
        :param max_duration: max duration of timer (in seconds). If not None, then timer will work backward
        (max_duration => 0)
        :type max_duration: float
        """
        self._start_time = None
        self._stop_time = None
        self._max_duration = max_duration

    @property
    def elapsed(self):
        if self._start_time is not None:
            if self._max_duration is None:
                return (time.time() - self._start_time) * 1000.0
            else:
                elapsed = (self._max_duration - (time.time() - self._start_time)) * 1000.0
                return 0.0 if elapsed <= 0.0 else elapsed

    def start(self):
        """
        Starts timer
        """
        if self._start_time is None:
            self._start_time = time.time()

    def stop(self):
        """
        Stops timer
        """
        self._stop_time = self.elapsed

    def reset(self):
        """
        Resets timer
        """
        self._start_time = None
