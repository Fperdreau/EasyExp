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

import sys
import time
import struct
import os
import select
import logging
from os.path import isfile


class Joystick(object):
    """
    Joystick wrapper class
    Handles joystick routines, such as calibration, position getter, etc.

    Usage:
    myJoyStick = Joystick()
    myJoyStick.init()
    """

    joy_response = True

    def __init__(self, calibration_file='joy_calibration.txt', input_file='/dev/input/js0', format='IhBB', calibration_time=5.0):
        """
        JoyStick constructor
        :param calibration_file: path to calibration file
        :type calibration_file: str
        :param input_file: path to device file
        :type input_file: str
        :param format: input file format (32 bit unsigned, 16 bit signed, 8 bit unsigned, 8 bit unsigned)
        :type format: str
        """

        # Create/open calibration file
        self._input_file = File(name=input_file)
        self._formatSize = struct.calcsize(format)
        self._calibrator = Calibration(self, calibration_file=calibration_file, max_time=calibration_time)

        self._format = format
        self._response_getter = None
        self._limits = None
        self.calibrated = False

        self._x = 0.0
        self._y = 0.0
        self._t = 0.0

    def init(self):
        """
        Initialize joystick
        :return:
        """
        if not self.calibrated:
            raise Exception('[{}] JoyStick must be calibrated before initialization'.format(__name__))

        # open /dev/input/js0 by default or the device given on the command line otherwise
        # open file in binary mode
        self._input_file.open()

        # discard everything in the joystick buffer at the moment
        self.flush()
        print('[{}] Joystick initialized'.format(__name__))

    def flush(self):
        """
        Clears the joystick input file
        """
        while len(select.select([self._input_file.handler.fileno()], [], [], 0.0)[0]) > 0:
            os.read(self._input_file.handler.fileno(), 4096)

    @property
    def position(self):
        """
        wait for a joystick move and set position variables x and y
        as soon as a new value is available
        :return: joystick position and timestamp (x, y, timestamp)
        :rtype: list
        """
        self._input_file.open()
        while len(select.select([self._input_file.handler.fileno()], [], [], 0.0)[0]) > 0:
            # while there is something to read from the joystick
            # non blocking read, maximum size: formatSize
            joy_event = os.read(self._input_file.handler.fileno(), self._formatSize)
            if len(joy_event) == self._formatSize:
                (self._t, value, dunno, axis) = struct.unpack(self._format, joy_event)
                if axis == 0:
                    self._x = value
                elif axis == 1:
                    self._y = value

        if self.calibrated:
            # Normalize to min/max
            if self._x < 0:
                self._x /= -float(self._limits['right'])
            else:
                self._x /= float(self._limits['left'])

            if self._y > 0:
                self._y /= float(self._limits['top'])
            else:
                self._y /= -float(self._limits['bottom'])

        return [self._x, self._y, self._t]

    def get_response(self, time_to_respond=10.0, response_threshold=0.4):
        """
        Get response from joystick
        :param response_threshold:
        :param time_to_respond:
        :return: response and response time
        :rtype: dict (response, response time)
        """
        if self._response_getter is None:
            self._response_getter = Response(device=self, time_to_respond=time_to_respond,
                                             response_threshold=response_threshold)
        return self._response_getter.response

    def calibrate(self):
        """
        Calibrates joystick
        :param max_time:
        :return:
        """
        self._limits = self._calibrator.calibrate()
        self.calibrated = True


class Calibration(object):
    """
    Calibration class
    Handles joystick calibration
    """

    def __init__(self, device=Joystick, calibration_file='joy_calibration.txt', max_time=30.0):
        """
        Calibration constructor
        :param device:
        :type device: Joystick
        :param max_time: maximum calibration time
        :type max_time: float
        """
        self.__device = device
        self.__file = File(name=calibration_file)
        self.__max_time = max_time

        self.__start_time = None
        self.__limits = {'left': 0.0, 'top': 0.0, 'right': 0.0, 'bottom': 0.0}
        self.__axis = {'left': None, 'top': None, 'right': None, 'bottom': None}

    def __str__(self):
        return ("[{}] Calibration results: {}".format(__name__,
                ' '.join(['{}: {}'.format(key, value) for key,value in self.__limits.iteritems()])))

    def calibrate(self):
        """
        Calibration routine
        """
        # Load previous calibration results
        self.load()

        # Perform calibration for each axis
        self.calibrate_axis()

        # Save calibration results
        self.save()

        print(self)
        return self.__limits

    def calibrate_axis(self):
        """
        Calibrate joystick
        User must move the joystick to the specified direction (top, right, bottom, left)
        :return:
        """
        print('[{}] Starting calibration'.format(__name__))

        for axis in self.__axis:
            print('[{}] Calibrating "{}" axis'.format(__name__, axis))
            if self.__start_time is None:
                self.__start_time = time.time()

            while True:
                new_position = self.__device.position
                sys.stdout.flush()

                if axis == 'top' and new_position[1] > self.__limits['top']:
                    self.__limits['top'] = new_position[1]
                if axis == 'right' and new_position[0] < self.__limits['right']:
                    self.__limits['right'] = new_position[0]
                if axis == 'bottom' and new_position[1] < self.__limits['bottom']:
                    self.__limits['bottom'] = new_position[1]
                if axis == 'left' and new_position[0] > self.__limits['left']:
                    self.__limits['left'] = new_position[0]

                if (time.time() - self.__start_time) > self.__max_time:
                    self.__start_time = None
                    self.__axis[axis] = True
                    break

        for axis, limit in self.__limits.iteritems():
            if limit == 0.0:
                raise Exception('Calibration failed')

        self.__start_time = None
        return self.__limits

    def load(self):
        """
        Read the values of the axis from the file joy_calibration obtained during calibration
        :rtype: bool
        """

        if isfile(self.__file.name):
            self.__file.open()
            self.__limits['right'] = int(self.__file.line)
            self.__limits['left'] = int(self.__file.line)
            self.__limits['top'] = int(self.__file.line)
            self.__limits['bottom'] = int(self.__file.line)
            return True
        else:
            return False

    def save(self):
        """
        Save calibration settings into file
        """
        self.__file.open()
        self.__file.write("{}\n".format(self.__limits['right']))
        self.__file.write("{}\n".format(self.__limits['left']))
        self.__file.write("{}\n".format(self.__limits['top']))
        self.__file.write("{}\n".format(self.__limits['bottom']))


class GraphicsJoy(Joystick):

    def __init__(self, calibration_file='joy_calibration.txt', input_file='/dev/input/js0', format='IhBB',
                 calibration_time=5.0, sensitivity=0.02, resolution=(1024, 768)):
        """
        GraphicsJoy constructor
        :param calibration_file:
        :param input_file:
        :param format:
        :param calibration_time:
        :param sensitivity:
        :param resolution:
        """
        super(GraphicsJoy, self).__init__(calibration_file=calibration_file, input_file=input_file, format=format,
                                          calibration_time=calibration_time)
        self._sensitivity = sensitivity
        self._resolution = resolution
        self._step = 0.01

    @property
    def sensitivity(self):
        return self._sensitivity

    @sensitivity.setter
    def sensitivity(self, value):
        if value < 0.0:
            value = 0.0
        self._sensitivity = value

    def set_sensitivity(self, direction=-1):
        self.sensitivity += direction * self._step

    @property
    def position(self):
        """
        wait for a joystick move and set position variables x and y
        as soon as a new value is available
        :return: joystick position and timestamp (x, y, timestamp)
        :rtype: list
        """
        self._input_file.open()
        while len(select.select([self._input_file.handler.fileno()], [], [], 0.0)[0]) > 0:
            # while there is something to read from the joystick
            # non blocking read, maximum size: formatSize
            joy_event = os.read(self._input_file.handler.fileno(), self._formatSize)
            if len(joy_event) == self._formatSize:
                (self._t, value, dunno, axis) = struct.unpack(self._format, joy_event)
                if axis == 0:
                    self._x = value
                elif axis == 1:
                    self._y = value

        if self.calibrated:
            # Normalize to min/max
            if self._x < 0:
                self._x /= -float(self._limits['right'])
            else:
                self._x /= float(self._limits['left'])

            if self._y > 0:
                self._y /= float(self._limits['top'])
            else:
                self._y /= -float(self._limits['bottom'])

            # Multiplies by -1 to match axis orientation of screen
            self._x *= -1*self._sensitivity * (self._resolution[0] * 0.5)
            self._y *= self._sensitivity * (self._resolution[1] * 0.5)

        return [self._x, self._y, self._t]


class Response(object):
    """
    Response getter
    """

    def __init__(self, device=Joystick, time_to_respond=None, response_threshold=0.4):
        """
        Response constructor
        :param device: instance of joystick device
        :type device: Joystick
        :param time_to_respond: maximum time to respond (in seconds)
        :type time_to_respond: float
        """
        self.__device = device
        self.__time_to_respond = time_to_respond
        self.__response_threshold = response_threshold
        self.time_out = False
        self.start_time = None
        self.response_time = None

    @property
    def response(self):
        """
        Returns response from joystick, response time and timeout status
        :rtype: {'response': [left, right, top, bottom], 'response_time': float, 'timeout': bool}
        """
        current_response = {'top': False, 'right': False, 'bottom': False, 'left': False}
        if self.start_time is None:
            self.start_time = time.time()

        # Get position
        new_position = self.__device.position

        # Compute elapsed response time
        self.response_time = time.time() - self.start_time

        current_response['left'] = new_position[0] > self.__response_threshold
        current_response['right'] = new_position[0] < -self.__response_threshold
        current_response['top'] = new_position[1] > self.__response_threshold
        current_response['bottom'] = new_position[1] < -self.__response_threshold

        # Did we get any response?
        response_given = False
        for direction, joy_status in current_response.iteritems():
            if joy_status:
                response_given = True
                break

        # If we did not and response time is over, then throw a timeout
        if not response_given and self.response_time > self.__time_to_respond:
            print("[{}] Warning: Response timeout".format(__name__))
            self.time_out = True

        # Reset timer if response has been given
        if response_given:
            self.start_time = None

        return {'response': current_response, 'response_time': self.response_time, 'timeout': self.time_out}


class File(object):
    """
    Handles input file and relates methods
    """

    def __init__(self, name):
        """
        File's construtor
        :param name:
        """
        self.name = name
        self.__handler = None

    def open(self):
        """
        Create the datafile and write the header
        :return:
        """
        try:
            self.__handler = open(self.name, 'a+b')
        except (IOError, TypeError) as e:
            msg = ("[{}] Could not open datafile: {}".format(__name__, self.name, e))
            logging.fatal(msg)
            raise IOError(msg)

    @property
    def handler(self):
        """
        File handler
        :return:
        """
        return self.__handler

    @property
    def line(self):
        """
        Returns current line
        :return:
        """
        if self.__handler is not None and not self.__handler.closed:
            return self.__handler.readline()

    def close(self):
        """
        Close data file
        :return:
        """
        if self.__handler is not None and not self.__handler.closed:
            self.__handler.close()

    def write(self, data_to_write):
        """
        Write to the datafile
        :param data_to_write:
        :return:
        """
        if self.__handler is not None and not self.__handler.closed:
            try:
                self.__handler.write(data_to_write)
            except (IOError, TypeError) as e:
                msg = ("[{}] Could not write into the user's datafile ({}): {}".format(__name__, self.name, e))
                logging.fatal(msg)
                raise IOError(msg)
        else:
            logging.warning('[{}] File has not been opened'.format(__name__))


if __name__ == "__main__":
    from psychopy import visual
    import numpy as np
    import pygame

    # Instantiate joystick
    joy = GraphicsJoy()

    # Calibrate joystick
    joy.calibrate()

    # Initialize joystick
    joy.init()

    # Open window
    win = visual.Window(
        size=(1400, 525),
        monitor='TestMonitor',
        color=(-1, -1, -1),
        units='pix',
        winType='pygame',
        pos=(0, 0),
        waitBlanking=True,
        fullscr=False)
    win.setMouseVisible(False)

    position = np.array((0.0, 0.0))
    cursor = visual.Rect(win, width=50, height=50, fillColor=(0.0, 0.0, 0.0), lineColor=None, units='pix', pos=position)

    # Get response
    response = None
    response_time = None
    init_time = time.time()
    while True:
        response = joy.get_response()
        for key, status in response['response'].iteritems():
            if status:
                print(key)

        position += np.array((joy.position[0], joy.position[1]))
        cursor.setPos(position)
        cursor.draw()

        win.flip()

        pygame.event.pump()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_DOWN]:
            if keys[pygame.K_UP]:
                joy.set_sensitivity(1)
            else:
                joy.set_sensitivity(-1)
            print('New sensitivity: {}'.format(joy.sensitivity))

        if keys[pygame.K_ESCAPE] or response['timeout']:
            break

    print('Response given: {} (elapsed: {})'.format(response,
          response['response_time']))

    win.close()
