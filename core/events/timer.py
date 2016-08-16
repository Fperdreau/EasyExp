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

"""
This file is for Timer class
"""

import time


class Timer(object):
    """
    Timer class
    Implements a simple timer with start, stop and reset methods

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

    def __init__(self):
        """
        Timer constructor
        """
        self._start_time = None
        self._stop_time = None

    @property
    def elapsed(self):
        if self._start_time is not None:
            return (time.time() - self._start_time) * 1000.0

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
