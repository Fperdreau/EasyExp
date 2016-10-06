#!/usr/bin/python
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


import threading
import logging


class ThreadManager(object):
    """
    ThreadManager
    Singleton class that handles threading
    """

    __instances = {}

    def add(self, label, target):
        """
        Add thread to watched list
        :param label: thread label
        :type label: str
        :param target: target function/method
        :type target: object
        :return:
        """
        if label not in self.__instances:
            self.__instances[label] = threading.Thread(target=target)
            logging.debug('[{}] Thread "{}" added successfully'.format(__name__, label))

    def get_instance(self, label):
        """
        Return thread
        :param label: thread label
        :type label: str
        :return: threading.Thread
        """
        if label in self.__instances:
            return self.__instances[label]

    def remove(self, label):
        """
        Join and delete thread
        :param label:
        :raise: RuntimeError
        """
        if label in self.__instances and self.__instances[label].isAlive():
            try:
                self.get_instance(label).join()
                logging.debug('[{}] Thread "{}" closed successfully'.format(__name__, label))
            except RuntimeError as e:
                msg = '[{}] Could not join thread "{}": {}'.format(__name__, label, e)
                logging.critical(msg)
                raise RuntimeError(msg)

            del self.__instances[label]

    def quit(self):
        """
        Close all threads
        :return:
        """
        for label in self.__instances:
            self.remove(label)
