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


class Joystick(object):
    """
    Joystick wrapper class
    Handles joystick routines, such as calibration, position getter, etc.

    Usage:
    >>> myJoyStick = Joystick()
    >>> myJoyStick.init()
    """

    joy_response = True

    def __init__(self, calibration_file='joy_calibration.txt', input_file='/dev/input/js0', format='IhBB'):
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
        self.__calibration_file = File(name=calibration_file)
        self.__input_file = File(name=input_file)
        self.__formatSize = struct.calcsize(format)
        self.__format = format
        self.__calibrator = None

        self.calibrated = False

        self.__x = 0.0
        self.__y = 0.0
        self.__t = 0.0

        self.xmin = 0.0
        self.xmax = 0.0
        self.ymin = 0.0
        self.ymax = 0.0

    def init(self):
        """
        Initialize joystick
        :return:
        """
        if not self.calibrated:
            raise Exception('[{}] JoyStick must be calibrated before initialization'.format(__name__))

        # I read the values of the axis from the file joy_calibration obtained during calibration
        self.__calibration_file.open()
        self.xmax = int(self.__calibration_file.line)
        self.xmin = int(self.__calibration_file.line)
        self.ymax = int(self.__calibration_file.line)
        self.ymin = int(self.__calibration_file.line)

        # open /dev/input/js0 by default or the device given on the command line otherwise
        # open file in binary mode
        self.__input_file.open()

        # discard everything in the joystick buffer at the moment
        self.flush()
        print('[{}] Joystick initialized'.format(__name__))

    def flush(self):
        """
        Clears the joystick input file
        """
        while len(select.select([self.__input_file.handler.fileno()], [], [], 0.0)[0]) > 0:
            os.read(self.__input_file.handler.fileno(), 4096)

    @property
    def position(self):
        """
        wait for a joystick move and set position variables x and y
        as soon as a new value is available
        :return: joystick position and timestamp (x, y, timestamp)
        :rtype: list
        """
        self.__input_file.open()
        while len(select.select([self.__input_file.handler.fileno()], [], [], 0.0)[0]) > 0:
            # while there is something to read from the joystick
            # non blocking read, maximum size: formatSize
            joy_event = os.read(self.__input_file.handler.fileno(), self.__formatSize)
            if len(joy_event) == self.__formatSize:
                (self.__t, value, dunno, axis) = struct.unpack(self.__format, joy_event)
                if axis == 0:
                    self.__x = value
                elif axis == 1:
                    self.__y = value

        return [self.__x, self.__y, self.__t]

    def get_response(self, time_to_respond):
        """
        Get response from joystick
        :param time_to_respond:
        :return: response and response time
        :rtype: list (response, response time)
        """
        start_time = time.time()
        running = True
        response = None
        resp_time = 0
        while running:
            time.sleep(.1)
            position = self.position
            if position[0] > 0.4 * self.xmax:
                response = -1
                running = False
                resp_time = time.time() - start_time
            if position[1] < 0.4 * self.xmin:
                response = 1
                running = False
                resp_time = time.time() - start_time
            elif time.time() - start_time > time_to_respond:
                print("[{}] WARNING: JOYSTICK TIMEOUT".format(__name__))
                response = 99
                running = False
                resp_time = time.time() - start_time
        return [response, resp_time]

    def calibrate(self, max_time=30.0):
        """
        Calibrates joystick
        :param max_time:
        :return:
        """
        if self.__calibrator is None:
            self.__calibrator = Calibration(self, max_time=max_time)

        self.xmin, self.xmax, self.ymin, self.ymax = self.__calibrator.calibrate()
        self.__calibration_file.open()
        self.__calibration_file.write("{}\n".format(self.xmax))
        self.__calibration_file.write("{}\n".format(self.xmin))
        self.__calibration_file.write("{}\n".format(self.ymax))
        self.__calibration_file.write("{}\n".format(self.ymin))

        print("[{}] Calibration results: Xmax: {}, Xmin: {}, Ymax: {}, Ymin: {}".format(
            __name__, self.xmax, self.xmin, self.ymax, self.ymin
        ))

        self.calibrated = True


class Calibration(object):
    """
    Calibration class
    Handles joystick calibration
    """

    def __init__(self, device=Joystick, max_time=30.0):
        """
        Calibration constructor
        :param device:
        :type device: Joystick
        :param max_time: maximum calibration time
        :type max_time: float
        """
        self.__device = device
        self.__max_time = max_time
        self.__start_time = None
        self.__limits = [0.0, 0.0, 0.0, 0.0]  # xmin, xmax, ymin, ymax

    def calibrate(self):
        """
        Calibrate joystick
        :return:
        """
        if self.__start_time is None:
            self.__start_time = time.time()
            
        print('[{}] Starting calibration'.format(__name__))
            
        running = True
        while running:
            position = self.__device.position
            time.sleep(.1)
            sys.stdout.flush()
            if position[1] > self.__device.ymax:
                self.__limits[3] = position[1]
            if position[1] < self.__device.ymin:
                self.__limits[2] = position[1]
            if position[0] > self.__device.xmax:
                self.__limits[1] = position[0]
            if position[0] < self.__device.xmin:
                self.__limits[0] = position[0]
            if (time.time() - self.__start_time) > self.__max_time:
                running = False

        self.__start_time = None
        return self.__limits


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
        self.running = False
        self.time_out = False
        self.start_time = None
        self.response_time = None

    @property
    def response(self):
        """
        Returns response from joystick, response time and timeout status
        :rtype: {'response': [left, right, top, bottom], 'response_time': float, 'timeout': bool}
        """
        response = [False, False, False, False]
        if self.start_time is None:
            self.start_time = time.time()

        # Get position
        position = self.__device.position

        # Compute elapsed response time
        self.response_time = time.time() - self.start_time

        response[0] = position[0] > self.__response_threshold * self.__device.xmax
        response[1] = position[1] < self.__response_threshold * self.__device.xmin
        response[2] = position[2] > self.__response_threshold * self.__device.ymax
        response[3] = position[3] < self.__response_threshold * self.__device.ymin

        # Did we get any response?
        response_given = True in response

        # If we did not and response time is over, then throw a timeout
        if not response_given and self.response_time > self.__time_to_respond:
            print("[{}] Warning: Response timeout".format(__name__))
            self.time_out = True

        # Reset timer if response has been given
        if response_given:
            self.start_time = None

        return {'response': response, 'response_time': self.response_time, 'timeout': self.time_out}


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
            self.__handler = open(self.name, 'w+b')
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
        if self.handler is not None and not self.handler.closed:
            return self.handler.readline()

    def close(self):
        """
        Close data file
        :return:
        """
        if self.handler is not None and not self.handler.closed:
            self.handler.close()

    def write(self, datatowrite):
        """
        Write to the datafile
        :param datatowrite:
        :return:
        """
        if self.handler is not None and not self.handler.closed:
            try:
                self.handler.write(datatowrite)
            except (IOError, TypeError) as e:
                msg = ("[{}] Could not write into the user's datafile ({}): {}".format(__name__, self.name, e))
                logging.fatal(msg)
                raise IOError(msg)
        else:
            logging.warning('[{}] File has not been opened'.format(__name__))


if __name__ == "__main__":
    # Instantiate joystick
    joy = Joystick()

    # Calibrate joystick
    joy.calibrate()
    
    # Initialize joystick
    joy.init()

    # Get response
    response = None
    response_time = None
    while response is None:
        [response, response_time] = joy.get_response(10.0)
    print('Response given: {} (elapsed: {})'.format(response, response))

