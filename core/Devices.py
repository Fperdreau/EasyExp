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
import types
import time
from os.path import isfile

from Config import ConfigFiles
import logging

from core.gui.gui_wrapper import GuiWrapper

__status__ = "Development"


class Devices(object):
    """
    Dependency container for devices
    """

    def __init__(self, exp_folder, base_name, cli=False):
        """
        Devices constructor
        :param exp_folder: path to experiment folder
        :type exp_folder: str
        :param base_name: data file base name
            i.e "path/to/folder/subject_name"
        :type base_name: str
        """
        self.__devices_file = ConfigFiles('{}/devices.json'.format(exp_folder))
        self.__loadable = isfile('{}/devices.json'.format(exp_folder))
        self.__base_name = base_name
        self.__logger = logging.getLogger('EasyExp')
        self.__cli = cli

        self.__devices = dict()
        self.__ptw = None

        # Get settings
        if self.__loadable:
            self.__get_settings()
        else:
            self.__logger.warning('[{}] We could not find "{}" file in the experiment folder. '
                                  'This means that you will not be able to use devices in your '
                                  'experiment.'.format(__name__, self.__devices_file.pathtofile))

    def init(self, ptw=None):
        """
        Instantiate and initialize devices
        """
        if not self.__loadable:
            return None

        # Load settings
        self.__devices_file.load()

        # Set windows pointer if provided
        if ptw is not None:
            self.set_ptw(ptw)

        # Add devices
        for device_name, params in self.__devices_file.data['devices'].iteritems():
            self.add(device_name, **params['options'])

    @staticmethod
    def __update_dict(obj, key, value):
        """
        Add/update key/value pair to dictionary
        :param obj: dictionary to update
        :param key: key to add/update
        :param value: value associated to key
        :return: updated dictionay
        :rtype: dict
        """
        if key in obj:
            obj[key] = value
        else:
            obj.update({key: value})
        return obj

    def __get_settings(self):
        """
        Get devices settings
        :return:
        """
        if not self.__loadable:
            self.__logger.warning('[{}] We could not find "{}" file in the experiment folder. '
                                  'This means that you will not be able to use devices in your '
                                  'experiment.'.format(__name__, self.__devices_file.pathtofile))
            return None

        self.__devices_file.load()

        if "settings" not in self.__devices_file.data:
            self.__devices_file.data['settings'] = dict()

        # Create/load settings for every device listed in devices.json
        settings = dict()
        for device in self.__devices_file.data['devices']:
            if device not in self.__devices_file.data['settings']:
                settings.update(self.get_field(device))
            elif device in self.__devices_file.data['settings']:
                settings.update({device: self.__devices_file.data['settings'][device]})

        # Overwrite previous settings
        self.__devices_file.data['settings'] = settings

        # Allow user to change settings
        data = {
            'settings': self.__devices_file.data['settings']
        }
        data = self.display(data, cli=self.__cli)

        # Update and save settings
        self.__devices_file.data['settings'].update(data['settings'])
        self.__devices_file.save()

    def __getitem__(self, item):
        """
        Return instance of device
        :param item:
        :type item: str
        :return:
        """
        if item.lower() in self.__devices:
            return self.__devices[item.lower()]

    def __iter__(self):
        """
        Return iterator
        :return:
        """
        for item in self.__devices:
            yield item

    def iteritems(self):
        """
        Return iterator
        :return:
        """
        for item, instance in self.__devices.iteritems():
            yield item, instance

    def set_ptw(self, ptw):
        """
        Set display pointer
        :param ptw:
        :return:
        """
        self.__ptw = ptw

    def add(self, device_name, **params):
        """
        Add device to container
        :param device_name: name of device
        :type device_name: str
        :param params: parameters passed to device's constructor
        :return:
        """
        if not self.__loadable:
            msg = '[{}] Devices cannot be added if there are not defined in devices.json. We could not find this ' \
                  'file'.format(__name__)
            self.__logger.exception(msg)
            raise Exception(msg)

        device = Devices.get_class(device_name)

        if device_name.lower() not in self.__devices \
                and self.__devices_file.data['settings'][device_name]['value'] != "off":

            if hasattr(device, "user_file"):
                user_file = '{}_{}_{}.txt'.format(self.__base_name, device_name,
                                                  time.strftime('%d-%m-%Y_%H%M%S'))
                params = self.__update_dict(params, "user_file", user_file)

            if hasattr(device, "dummy_mode"):
                dummy_mode = self.__devices_file.data['settings'][device_name]['value'] == 'dummy'
                params = self.__update_dict(params, "dummy_mode", dummy_mode)

            if hasattr(device, "ptw"):
                params = self.__update_dict(params, "ptw", self.__ptw)

            # Instantiate device
            try:
                self.__devices[device_name.lower()] = device(**params)
                self.__logger.info('Device "{}" successfully added.'.format(device_name.upper()))
            except AttributeError as e:
                msg = AttributeError('Could not instantiate {}: {}'.format(device_name, e))
                self.__logger.critical(msg)
                raise AttributeError(msg)

            # Start device if not self-started
            if hasattr(self.__devices[device_name.lower()], 'run'):
                try:
                    self.__devices[device_name.lower()].run()
                    self.__logger.info('Device "{}" successfully started.'.format(device_name.upper()))
                except RuntimeError as e:
                    msg = AttributeError('Could not start {}: {}'.format(device_name, e))
                    self.__logger.critical(msg)
                    raise RuntimeError(msg)

    def close_all(self):
        """
        Close all devices
        :return:
        """
        for device in self.__devices:
            self.close(device)

    def close(self, device):
        """
        Close device
        :param device: device name
        :return:
        """
        lower = device.lower()
        if lower in self.__devices:
            if hasattr(self.__devices[lower], "close"):
                self.__logger.info('[{}] Closing "{}"'.format(__name__, device))
                self.__devices[lower].close()

    def delete(self, device_name):
        """
        Removed device
        :param device_name: device label
        :type device_name: str
        :return:
        """
        if device_name.lower() in self.__devices:
            del self.__devices[device_name.lower()]

    @staticmethod
    def get_class(method_name):
        """
        Instantiate class from class's name
        :param method_name: lass' name
        :type method_name: str
        :return:
        """
        # Import method implementation
        method_path = "core.apparatus.{}.{}".format(method_name.lower(), method_name.lower())
        try:
            mod = __import__(method_path, fromlist=method_name)
            method = getattr(mod, method_name)
            if isinstance(method, (types.ClassType, types.TypeType)):
                return method
            raise TypeError("%s is not a class." % method_name)
        except ImportError as e:
            msg = ImportError('[{}] Could not import "{}": {}'.format(__name__, method_name, e))
            logging.getLogger('EasyExp').critical(msg)
            raise msg

    @staticmethod
    def get_field(name):
        """
        Get field
        :param name:
        :type name: str
        :rtype: dict
        """
        return {
            name: {
                "type": "select",
                "options": [
                    "on",
                    "off",
                    "dummy"
                ],
                "value": "off",
                "label": name.capitalize()
            },
        }

    @staticmethod
    def display(data_to_load, cli=False):
        """
        Display settings and allow user to modify them
        :param data_to_load: dictionary to display and modify
        :type data_to_load: dict
        :param cli: View
        :type cli: bool
        :rtype: dict
        """
        if cli is True:
            info = GuiWrapper.factory(cli, 'nested', data_to_load, title="Devices Setup", mandatory=False)
        else:
            info = GuiWrapper.factory(cli, 'nested', data_to_load, title="Devices Setup")
        return info.out
