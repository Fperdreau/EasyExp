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
import logging


class Pause(object):
    """
    Pause class

    Handles pauses
    Pauses can be automatically triggered after a given number of completed trials or after a particular delay.
    """

    __allowed_mode = ('time', 'count')

    def __init__(self, mode='time', interval=0.0, logger=None):
        """
        Class constructor
        :param pause_mode: pause mode ('time' or 'count')
        :param interval:
        :param logger:
        """
        if mode.lower() not in self.__allowed_mode:
            raise AttributeError('Invalid pause mode')
        else:
            self.__mode = mode.lower()
            if mode == 'time':
                self.__handler = PauseTimer(interval=interval)
            elif mode == "count":
                self.__handler = PauseCounter(interval=interval)

        self.__elapsed = 0.0
        self.__nb_pause = 0
        self.__logger = logger if logger is not None else logging.getLogger('EasyExp')

    def run(self, force=False):
        """
        Is it time to do a break?
        :return:
        """
        if force or self.__handler.status:
            self.__logger.info("[{0}] {1}".format(__name__, self.__handler.text))
            # self.__handler.reset()
            return True
        else:
            return False

    @property
    def text(self):
        return self.__handler.text


class BasePauseHandler(object):

    @property
    def elapsed(self):
        """
        Time elapsed since last break
        :return:
        """
        raise NotImplementedError('Should implement this')

    @property
    def status(self):
        """
        Get elapsed time since last break
        :return:
        """
        raise NotImplementedError('Should implement this')

    @property
    def text(self):
        raise NotImplementedError('Should implement this')

    def reset(self):
        """
        Reset timer
        :return:
        """
        raise NotImplementedError('Should implement this')


class PauseTimer(BasePauseHandler):
    """
    Pause class

    Handles pauses
    Pauses can be automatically triggered after a given number of completed trials or after a particular delay.
    """

    def __init__(self, interval):
        """
        Class constructor
        :param interval: time interval between breaks
        """
        self.__interval = interval
        self.__counter = None

    @property
    def elapsed(self):
        """
        Time elapsed since last break
        :return:
        """
        if self.__counter is not None:
            return time.time() - self.__counter
        else:
            return 0.0

    @property
    def status(self):
        """
        Get elapsed time since last break
        :return:
        """
        if self.__counter is None:
            self.__counter = time.time()
            return False
        else:
            return self.elapsed >= self.__interval

    @property
    def text(self):
        return "Pause Requested - {0:1.2f} seconds have elapsed since last break".format(self.elapsed)

    def reset(self):
        """
        Reset timer
        :return:
        """
        self.__counter = None


class PauseCounter(BasePauseHandler):
    """
    Pause class

    Handles pauses
    Pauses can be automatically triggered after a given number of completed trials or after a particular delay.
    """

    def __init__(self, interval):
        """
        Class constructor
        :param interval: Number of completed trials between breaks
        """
        self.__interval = interval
        self.__counter = 0

    @property
    def elapsed(self):
        """
        Number of completed trials since last break
        :return:
        """
        return self.__counter

    @property
    def status(self):
        """
        Get elapsed time since last break
        :return:
        """
        if self.__counter >= self.__interval:
            return True
        else:
            self.__counter += 1
            return False

    @property
    def text(self):
        return "Pause Requested - {} trials completed since last break".format(self.__counter)

    def reset(self):
        """
        Reset timer
        :return:
        """
        self.__counter = 0

if __name__ == '__main__':

    pause = Pause(mode='time', interval=10.0)

    while True:
        if pause.run():
            print(pause.text)
            break
