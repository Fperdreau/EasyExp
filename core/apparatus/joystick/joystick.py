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
    >>> myJoyStick = Joystick()
    >>> myJoyStick.init()
    """

    joy_response = True

    def __init__(self, calibration_file='joy_calibration.txt', input_file='/dev/input/js0', format='IhBB', sensitivity=1.0, calibration_time=5.0):
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
        self.__input_file = File(name=input_file)
        self.__formatSize = struct.calcsize(format)
        self.__calibrator = Calibration(self, calibration_file=calibration_file, max_time=calibration_time)

        self.__format = format
        self.__response_getter = None
        self.__limits = None
        self.calibrated = False

        self.__x = 0.0
        self.__y = 0.0
        self.__t = 0.0


    def init(self):
        """
        Initialize joystick
        :return:
        """
        if not self.calibrated:
            raise Exception('[{}] JoyStick must be calibrated before initialization'.format(__name__))

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

        if self.calibrated:
            # Normalize to min/max      
            if self.__x < 0:
                self.__x /= -float(self.__limits['right'])
            else:
                self.__x /= float(self.__limits['left'])
            
            if self.__y > 0:
                self.__y /= float(self.__limits['top'])
            else:
                self.__y /= -float(self.__limits['bottom'])
                
        return [self.__x, self.__y, self.__t]

    def get_response(self, time_to_respond=10.0, response_threshold=0.4):
        """
        Get response from joystick
        :param time_to_respond:
        :return: response and response time
        :rtype: dict (response, response time)
        """
        if self.__response_getter is None:
            self.__response_getter = Response(device=self, 
                                              time_to_respond=time_to_respond, 
                                              response_threshold=response_threshold)
        return self.__response_getter.response

    def calibrate(self):
        """
        Calibrates joystick
        :param max_time:
        :return:
        """
        self.__limits = self.__calibrator.calibrate()
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
                position = self.__device.position
                sys.stdout.flush()

                if axis == 'top' and position[1] > self.__limits['top']:
                    self.__limits['top'] = position[1]
                if axis == 'right' and position[0] < self.__limits['right']:
                    self.__limits['right'] = position[0]
                if axis == 'bottom' and position[1] < self.__limits['bottom']:
                    self.__limits['bottom'] = position[1]
                if axis == 'left' and position[0] > self.__limits['left']:
                    self.__limits['left'] = position[0]
                
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
        response = {'top': False, 'right': False, 'bottom': False, 'left': False}
        if self.start_time is None:
            self.start_time = time.time()

        # Get position
        position = self.__device.position
        print(position)
        # Compute elapsed response time
        self.response_time = time.time() - self.start_time

        response['left'] = position[0] > self.__response_threshold
        response['right'] = position[0] < -self.__response_threshold
        response['top'] = position[1] > self.__response_threshold
        response['bottom'] = position[1] < -self.__response_threshold

        # Did we get any response?
        response_given = False
        for key, status in response.iteritems():
            if status:
                response_given = True
                break

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

    def write(self, datatowrite):
        """
        Write to the datafile
        :param datatowrite:
        :return:
        """
        if self.__handler is not None and not self.__handler.closed:
            try:
                self.__handler.write(datatowrite)
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
    while True:
        response = joy.get_response()
        for key, status in response['response'].iteritems():
            if status:
                print(key)
        
        if response['timeout']:
            break
        
    print('Response given: {} (elapsed: {})'.format(response, response['response_time']))

