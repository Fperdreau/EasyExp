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
import numpy as np
from psychopy import core


class FpsCounter(object):
    """
    FpsCounter class
    Measure FPS and screen flip duration

    requirements: PsychoPy
    """

    def __init__(self, ptw):
        """
        FpsCounter constructor
        Parameters
        ----------
        ptw: screen (PsychoPy) pointer
        """
        self.__ptw = ptw
        self.__frame_count = 0
        self.__init_time = time.time()
        self.__samples = np.array([])

    def flip(self, clear_buffer=True):
        """
        Flips screen and measures flip duration
        :param clear_buffer: should we clear the buffer on screen flip
        :type clear_buffer: bool
        """
        t0 = core.getTime()
        self.__ptw.flip(clearBuffer=clear_buffer)
        t1 = core.getTime()
        self.__samples = np.append(self.__samples, [round((t1 - t0) * 1000)])
        self.__frame_count += 1

    @property
    def fps(self):
        return round(self.__frame_count/self._time, 1)

    @property
    def _time(self):
        return time.time() - self.__init_time

    @property
    def _frame_duration(self):
        return np.mean(self.__samples)

    def __str__(self):
        return 'FPS: {} [{} samples, t={} s] -- frame duration: {} ms'.format(self.fps, self.__frame_count, self._time,
                                                                              self._frame_duration)
