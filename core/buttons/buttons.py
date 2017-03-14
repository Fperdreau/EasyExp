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

import psychopy
import pygame
import time

__version__ = '1.1.0'


class InputDevice(object):
    """
    Handles input device instance and watcher
    """

    # List of allowed device
    allowed_devices = {'mouse', 'keyboard'}

    def __init__(self, device, **kwargs):
        """
        InputDevice constructor
        :param device: name of device
        :type device: str
        :param kwargs: argument passed to device's constructor
        """
        if device not in InputDevice.allowed_devices:
            raise TypeError('"{} is not a valid device. Possible options are: "'.format(device,
                                                                                        ','.join(InputDevice.allowed_devices)))
        self.__device = device
        self.__status = None
        self.__args = kwargs
        self.__instance = None

    @property
    def instance(self):
        """
        Returns device's instance (singleton)
        :return:
        """
        if self.__instance is None:
            if self.__device == 'keyboard':
                self.__instance = pygame.key
            elif self.__device == 'mouse':
                self.__instance = psychopy.event.Mouse(**self.__args)
        return self.__instance

    def update(self):
        """
        Updates device's status
        """
        pygame.event.pump()
        if self.__device == 'keyboard':
            self.__status = self.instance.get_pressed()
        else:
            self.__status = self.instance.getPressed()

        pygame.event.clear()

    def status(self, code):
        """
        Get key status
        :param code: key code
        :type code: int
        :return: key status
        :rtype: bool
        """
        return self.__status[code] == 1

    @property
    def position(self):
        """
        Get device position (only for mouse; otherwise returns None)
        position: tuple
        :return: cursor position (mouse only)
        :rtype: tuple, None
        """
        if hasattr(self.instance, 'getPos'):
            return self.instance.getPos()
        else:
            return None


class UserInput(object):
    """
    UserInput class: Observer pattern
    Handles inputs devices (mouse, keyboard) and update status of watched keys

    Usage:
    # Create instance
    Inputs = UserInput()
    Inputs.add_device('keyboard')  # arguments are (device type, device arguments: optional)
    Inputs.add_device('mouse', visible=False, newPos=None, win=win)

    # Add listeners
    Inputs.add_listener('keyboard', 'a', K_a)  # arguments are: device_type, key label, key code (Pygame constant)
    Inputs.add_listener('keyboard', 'quit', K_ESCAPE)
    Inputs.add_listener('mouse', 'left', 0)

    # Update status
    Inputs.update()

    # Access watched key's status
    Inputs.get_status('a')

    """

    def __init__(self):
        """
        UserInput constructor
        """
        self._listeners = dict()
        self._devices = dict()
        self._behavior = dict()

    def add_device(self, device, **kwargs):
        """
        Add a device to the watch list
        :param device: device name
        :type device: str
        :param kwargs: arguments passed to device's constructor
        """
        if device not in self._devices:
            self._devices[device] = InputDevice(device, **kwargs)

    def update(self):
        """
        Update devices' state
        :return:
        """
        for label, device in self._devices.iteritems():
            device.update()

    def add_listener(self, device, name, code, target=None, **kwargs):
        """
        Add a listener
        :param target:
        :param device: name of device
        :type device: str
        :param name: name of listener
        :type name: str
        :param code: key code
        :type code: int
        :return:
        """
        if name not in self._listeners:
            self._listeners.update({
                name: {
                    'device': device,
                    'code': code
                }
            })

            if target is not None:
                self._behavior.update({
                    name: {
                        'target': target,
                        'args': kwargs
                    }
                })

    def remove_listener(self, name):
        """
        Remove listener from watch list
        :param name: name of listener
        :return: success or failure
        :rtype: bool
        """
        if name in self._listeners:
            del self._listeners[name]
            return True
        else:
            return False

    def remove_all(self):
        """
        Remove all listeners
        :return:
        """
        for device in self._listeners:
            del device

    def get_status(self, name):
        """
        Get listener status
        :param name: name of listener
        :return: status of listener
        :rtype: bool
        """
        if name in self._listeners:
            status = self._devices[self._listeners[name]['device']].status(self._listeners[name]['code'])
            if status:
                self._trigger(name)
            return status
        else:
            raise Exception('"{}" is not present in the listeners list. You must add it by calling '
                            'UserInput.add_listener() method')

    def get_position(self, name):
        """
        Get listener position
        :param name: name of listener
        :return: position of listener
        :rtype: bool
        """
        if name in self._listeners:
            return self._devices[self._listeners[name]['device']].position
        else:
            raise Exception('"{}" is not present in the listeners list. You must add it by calling '
                            'UserInput.add_listener() method')

    def _trigger(self, name):
        """
        Execute function binded to event
        :param name:
        :return:
        """
        if name in self._behavior:
            try:
                self._behavior[name]['target'](**self._behavior[name]['args'])
            except Exception as e:
                raise Exception(e)


class SlowUserInput(UserInput):
    """
    SlowUserInput class
    Inherits from UserInput class

    This class simply implement a down-sampled version of UserInput class
    """

    def __init__(self, sampling=60.0):
        """
        SlowUserInput constructor
        :param sampling: desired sampling rate (in Hz)
        :type sampling: float
        """
        super(SlowUserInput, self).__init__()
        self.__timer = None
        self.__sampling = float(sampling)
        self.__min_dt = 1/self.__sampling

    @property
    def time_to_update(self):
        """
        Check if it is time to update key status
        :return: True or False
        :rtype: bool
        """
        if self.__timer is None:
            self.__timer = time.time()
        status = (time.time() - self.__timer) >= self.__min_dt
        if status:
            self.__timer = time.time()
        return status

    def get_status(self, name):
        """
        Get listener status
        :param name: name of listener
        :return: status of listener
        :rtype: bool
        """
        if name in self._listeners:
            if self.time_to_update:
                status = self._devices[self._listeners[name]['device']].status(self._listeners[name]['code'])
                if status:
                    self._trigger(name)
                return status
            else:
                return False
        else:
            raise Exception('"{}" is not present in the listeners list. You must add it by calling '
                            'UserInput.add_listener() method')


class Buttons(object):
    """
    Buttons class
    Handles keyboard/mouse inputs
    """

    allowed = {'mouse', 'keyboard'}

    def __init__(self, ptw, device, buttons):
        """
        :param device
        :param dict buttons:
        :return:
        """
        if device not in self.allowed:
            raise("'{}' is not supported.".format(device))

        self.device_type = device
        if device == 'keyboard':
            self.device = pygame.key
        elif device == 'mouse':
            self.device = psychopy.event.Mouse(visible=False, newPos=None, win=ptw)

        self.buttons = buttons
        self.status = {}
        self.init_buttons()

    def init_buttons(self):
        """
        Reset every buttons status to their initial value
        :return:
        """
        for button, ind in self.buttons.iteritems():
            self.status[button] = False

    def get(self):
        """
        Get buttons state
        :return:
        """
        self.init_buttons()
        pygame.event.clear()
        pygame.event.pump()
        if self.device == 'keyboard':
            keys = self.device.get_pressed()
        else:
            keys = self.device.getPressed()

        for button, ind in self.buttons.iteritems():
            self.status[button] = keys[ind] == 1
        pygame.event.clear()

    @property
    def position(self):
        """
        Get device position (only for mouse; otherwise returns None)
        Returns
        -------
        position: tuple
        """
        if self.device_type == 'mouse':
            return self.device.getPos()
        else:
            return None


if __name__ == '__main__':
    # Example

    from psychopy import visual
    from pygame import *
    import time

    # Window
    win = visual.Window(
        size=(800, 600),
        monitor='TestMonitor',
        color=(-1, -1, -1),
        pos=(0, 0),
        units='pix',
        winType='pygame',
        fullscr=False)

    # list of keys (only to facilitate prints within the loop)
    key_list = ('a', 'quit', 'left', 'right')

    # Create instance
    Inputs = UserInput()
    Inputs.add_device('keyboard')
    Inputs.add_device('mouse', visible=False, newPos=None, win=win)

    # Add listeners
    Inputs.add_listener('keyboard', 'a', K_a)
    Inputs.add_listener('keyboard', 'quit', K_ESCAPE)
    Inputs.add_listener('mouse', 'left', 0)
    Inputs.add_listener('mouse', 'right', 2)

    init_time = time.time()
    duration = 5.0  # Loop duration
    while (time.time() - init_time) < duration:
        # Update devices' state
        Inputs.update()
        for key in key_list:
            if Inputs.get_status(key):
                print('{} pressed: {}'.format(key, Inputs.get_status(key)))

    win.close()
