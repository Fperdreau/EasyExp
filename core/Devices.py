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

"""
This file is for Devices class - dependencies container
"""

from __future__ import print_function
import sys
import types

import time

from Config import ConfigFiles
import logging

from Core import Core

__status__ = "Development"


class Devices(object):
    """
    Dependency container for devices
    """

    def __init__(self, core=Core):
        """
        Devices constructor
        :param core: EasyExp.core instance
        :type core: Core
        """
        self.__core = core
        self.devices = dict()
        self.devices_file = ConfigFiles('{}/devices.json'.format(core.folders['expFolder']))
        self.settingsFile = core.config
        self.__logger = logging.getLogger('EasyExp')

    def init(self):
        """
        Instantiate and initialize devices
        """
        self.devices_file.load()
        for device_name, params in self.devices_file.data.iteritems():
            self.add_device(device_name, **params)

    def add_device(self, device_name, **params):
        """
        Add device to container
        :param device_name: name of device
        :type device_name: str
        :param params: parameters passed to device's constructor
        :return:
        """
        device = Devices.str_to_class(device_name)
        if device_name not in self.devices and self.settingsFile.data['device'][device_name] is not False:
            try:
                if hasattr(device, "user_file"):
                    user_file = '{}/{}_{}.txt'.format(self.__core.user.dftName, device_name,
                                                      time.strftime('%d-%m-%Y_%H%M%S'))
                    params.update({"user_file": user_file})

                if hasattr(device, "ptw"):
                    params.update({"ptw": self.__core.screen.ptw})

                self.devices[device_name] = device(**params)
            except AttributeError:
                raise AttributeError('Could not instantiate {}'.format(device_name))

    def del_device(self, device_name):
        """
        Removed device
        :param device_name: device label
        :type device_name: str
        :return:
        """
        if device_name in self.devices:
            del self.devices[device_name]

    @staticmethod
    def str_to_class(field):
        """
        Instantiate class from class's name
        :param field: class' name
        :type field: str
        """
        try:
            identifier = getattr(sys.modules[__name__], field)
        except AttributeError:
            raise NameError("%s doesn't exist." % field)
        if isinstance(identifier, (types.ClassType, types.TypeType)):
            return identifier
        raise TypeError("%s is not a class." % field)
