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

import time
import numpy as np
from sledclient import SledClient
from sledclientsimulator import *
from ...com.fpclient.fpclient import FpClient

import logging

__version__ = '1.1.4'


class Sled(object):
    """
    MySled is a Wrapper class that handles SLED's routine relying on FPClient and SledClient. It also implements a
    dummy mode that simulates SLED's displacement when the SLED is not actually connected (Usefull for developing or
    debugging experiments).

    Example:
    >>>duration = 1.0  # Movement duration in seconds
    >>>sled = Sled(status=True, server='sled', port=3375)  # Instantiate Sled
    >>>sled.move(0.20, duration)  # Send commands to the SLED
    >>>init_time = time.time()
    >>>while time.time() <= (init_time + duration):
    >>>     print('Sled position: {}'.format(sled.getposition(t=sled.client.time())))  # Get and print SLED's position
    >>>sled.close()  # Quit and disconnect SLED client

    Requirements:
    - FPClient
    - SledClient
    - sledclientsimulator
    """

    mvt_back_duration = 2.0
    home = 0.0
    dummy_mode = False

    def __init__(self, dummy_mode=False, server=False, port=3375, logger=None):
        """
        MySled constructor
        Parameters
        ----------
        :param dummy_mode: if false, connects to actual FPClient server, otherwise runs in dummy mode
        :type dummy_mode: bool
        :param server: IP address of sled server
        :type server: bool|str
        :param port: com port
        :type port: int
        """
        self.dummy_mode = dummy_mode
        self.port = port
        self.server = server
        self.__position_tracker = PositionTracker()
        self.__validator = None
        self.__logger = logger if logger is not None else logging.getLogger('EasyExp')
        self.client = None
        self.positionClient = None
        self.position = [0.0, 0.0]
        self.timer = None
        self.lightStatus = True  # The Sled lights should be off before initialization
        self.moveType = 'Sinusoid'  # Default profile

        # Connect to sled server
        self.connectSledServer()

    def connectSledServer(self):
        """
        Connects to sled Server (server=True) or simulate a sled server (server=False)
        """
        if self.dummy_mode:
            self.__logger.warning('[{}] !!! Sled running in dummy mode !!!'.format(__name__))
            self.client = DummyClient()  # for visual only mode
        else:
            try:
                self.client = SledClient()  # derived from FPClient
                self.client.connect(self.server, self.port)
                self.lights(True)
            except Exception as e:
                raise Exception('[{0}] Could not connect to the Sled client: {1}'.format(__name__, e))
        self.client.startStream()
        time.sleep(2)

        # homing sled at -reference
        if not self.at_position(self.home):
            self.client.goto(self.home, self.mvt_back_duration)
            time.sleep(self.mvt_back_duration)

    def connectPositionServer(self, server=None):
        """
        Connect to a First Principles server which returns the viewer position in the first marker position.
        Make sure this function is called after connectSledServer so that the fall back option is present.
        :param server:
        """
        self.__logger.debug("requested position server: " + str(server))
        if not server:
            self.positionClient = self.client
        elif server == "mouse":
            return
        else:
            self.positionClient = FpClient()  # make a new NDI First Principles client
            self.positionClient.startStream()  # start the synchronization stream.
            time.sleep(2)

    def move(self, pos, duration, movetype='Sinusoid'):
        """
        Move the Sled to the requested position and start the timer

        :param movetype: sled profile
        :type movetype: str
        :param pos: final sled position
        :type pos: float
        :param duration: movement duration
        :type duration: float

        :return: void
        """
        self.timer = time.time()
        self.moveType = movetype
        self.client.goto(pos, duration)

    @property
    def is_moving(self):
        return self.__position_tracker.is_moving

    def at_position(self, position, tolerance=0.01):
        """
        Check if sled has been at the specified location during a given period of time
        :param position: position to test
        :type position: float (in m)
        :param tolerance: tolerated deviance from expected position
        :type tolerance: float (in m)
        :return: Sled at position and not moving
        :rtype: bool
        """
        distance = np.abs(self.getposition()[0] - position)
        return distance <= tolerance and not self.is_moving

    def wait_ready(self, position, duration):
        """
        Check if sled is at expected position. If not, then command sled to move to this position.
        :param position: expected position
        :type position: float (in m)
        :param duration: movement duration
        :type duration: float (in s)
        :return: Sled is at expected position
        :rtype: bool
        """
        if self.validate():
            if not self.at_position(position):
                self.__logger.debug('Sled not at expected position: {} instead of {}'.format(self.position[0], position))
                self.move(position, duration)
                return False
            else:
                self.__logger.debug('Sled ready and on expected position: {}'.format(self.position[0]))
                return True
        else:
            return False

    def stop(self):
        """
        Stop the sled movement and stop the timer

        :return: void
        """
        self.client.sendCommand('{} stop'.format(self.moveType))
        duration = time.time() - self.timer
        self.timer = time.time()
        self.__logger.debug('[{0}] Sled duration: {1} seconds'.format(__name__, duration))
        return duration

    def close(self):
        """
        Close connection with the Sled Client

        :return: void
        """
        # Return to home position
        while not self.wait_ready(position=self.home, duration=self.mvt_back_duration):
            pass

        # Switch lights on
        self.lights(True)

        # Close clients
        self.__logger.info("[{}] Closing Sled client".format(__name__))  # logger may not exist anymore
        try:
            self.client.stopStream()
        except Exception:
            raise Exception('[{}] Could not stop client stream')

        if hasattr(self, "positionClient") and hasattr(self.positionClient, "stopStream"):
            self.__logger.info("[{}] closing Position client".format(__name__))  # logger may not exist anymore
            try:
                self.positionClient.stopStream()
            except Exception:
                raise Exception('[{}] Could not stop positionClient stream')

        self.__logger.info('[{}] Stream successfully stopped'.format(__name__))

        self.client.sendCommand('Bye')
        self.client.__del__()

    def getposition(self, t=None, dt=None):
        """
        Get sled position
        :return: numpy matrix
        """
        pp = self.client.getPosition(t=t, dt=dt)
        self.position = np.array(pp).ravel().tolist()  # python has too many types
        self.__position_tracker.add_history(self.position[0])
        return self.position

    def getvelocity(self):
        return self.__position_tracker.velocity

    def lights(self, status=True):
        """
        Switches SLED lights on or off
        Parameters
        ----------
        @param status: new light status
        @type status: bool

        Returns
        -------
        void
        """
        self.lightStatus = status
        if self.lightStatus:
            self.client.sendCommand("Lights On")
        else:
            self.client.sendCommand("Lights Off")

    def validate(self, threshold_time=0.200):
        """
        Validate position
        :param threshold_time:
        :return:
        """
        if self.__validator is None:
            self.__validator = Validator(self, threshold_time=threshold_time)
        return self.__validator.validate()

    def reset_validator(self):
        """
        Reset position validator
        :return:
        """
        self.__validator = None

    def __str__(self):
        return 'Position: {0: 1.3f} m | Velocity: {1: 1.3f} m/s: Moving: {2}'.format(self.position[0],
                                                                                     self.getvelocity(),
                                                                                     self.is_moving)


class Validator(object):
    """
    Validator Class
    Validate position over a given period of time
    """

    def __init__(self, tracker, threshold_time=0.100):
        """
        Class constructor
        :param tracker: sled instance
        :type tracker: Sled
        :param threshold_time:
        """
        self.__tracker = tracker
        self.threshold_time = threshold_time
        self.valid_time = None
        self.validated = False
        self.validated_position = None

    def validate(self):
        """
        validate position
        :rtype: bool
        """
        if self.validated:
            self.reset()

        self.__tracker.getposition()

        if not self.__tracker.is_moving:
            if self.valid_time is None:
                self.validated = False
                self.valid_time = time.time()

            elif (time.time() - self.valid_time) >= self.threshold_time:
                self.validated_position = self.__tracker.getposition()[0]
                self.validated = True
        else:
            # Restart the timer
            self.reset()

        return self.validated

    def reset(self):
        """
        Reset validator
        :return:
        """
        self.valid_time = None
        self.validated = False


class PositionTracker(object):
    """
    PositionTracker class: track positions of sled over time, compute current velocity and estimate motion state
     (is moving or not)
    """
    __max_positions = 3
    __time_interval = 0.01
    __velocity_threshold = 0.001

    def __init__(self):
        self.__history = []
        self.__previous = []
        self.__position = []
        self.__intervals = []
        self.__dt = 0.0
        self.__tOld = None
        self.__nb_positions = 0

    @property
    def dt(self):
        if self.__tOld is None:
            self.__tOld = time.time()

        try:
            if self.__tOld is not None:
                self.__dt = time.time() - self.__tOld
        except TypeError as e:
            logging.getLogger('EasyExp').warning(e)

        return self.__dt

    def __reset(self):
        """
        Reset timer
        :return:
        """
        self.__dt = 0.0
        self.__tOld = None

    def add_history(self, position):
        """
        Add new position to sensor's position history in order to compute statistics
        :return:
        """
        if self.dt >= self.__time_interval:

            if self.__nb_positions == 0:
                self.__history = np.array(position)
                self.__intervals = np.array(self.dt)
            else:
                if self.__nb_positions < self.__max_positions:
                    old = self.__history
                    self.__history = np.vstack((old, position))

                    old_dts = self.__intervals
                    self.__intervals = np.vstack((old_dts, self.dt))
                else:
                    old = self.__history[range(1, self.__max_positions)]
                    self.__history = np.vstack((old, position))

                    old_dts = self.__intervals[range(1, self.__max_positions)]
                    self.__intervals = np.vstack((old_dts, self.dt))

            self.__nb_positions += 1

            # Reset timer
            self.__reset()

        return self.__history

    @property
    def velocity(self):
        """
        Get velocity
        :rtype: float
        """
        if self.__nb_positions >= self.__max_positions:
            distances = [self.distance(self.__history[i], self.__history[j]) for i, j
                         in zip(range(0, self.__max_positions - 1), range(1, self.__max_positions))]

            return float(np.mean(np.array(distances) / np.array(self.__intervals)))
        else:
            return 0.0

    @property
    def is_moving(self):
        """
        Check if sensor is moving
        :return: sensor is moving (True)
        """
        return self.velocity > self.__velocity_threshold

    @staticmethod
    def distance(init, end):
        """
        Compute spherical distance between two given position
        :param init:
        :type init: float
        :param end:
        :type end: float
        :return:
        """
        return math.sqrt((end - init)**2)


class DummyClient(SledClientSimulator):
    """
    Dummy Mode of the Sled. Simulates movements
    Simply overrides SledClientSimulator methods to fake sled movement
    """
    def __init__(self):
        """
        DummyClient constructor
        """
        super(DummyClient, self).__init__()
        self.tOld = None
        self._endTime = 0.0
        self._movPos = 0.0
        self._speed = 0.0
        self._position = 0.0
        self._requestedPos = 0.0
        self._duration = 0.0
        self._distance = 0.0
        self._direction = 1

    def connect(self):
        pass

    def startStream(self):
        pass

    def stopStream(self):
        pass

    def getposition(self, mode='visual'):
        pass

    def __del__(self):
        pass

    def sendCommand(self, body):
        """
        Sends command to sled
        Parameters
        ----------
        @param body: command
        @type body: str

        Returns
        -------

        """
        # Parse body
        command = body.split(' ')
        if command[0] == 'Sinusoid' and command[1] != "stop":
            self._requestedPos = float(command[1])
            self._distance = self._requestedPos - self._position
            self._duration = float(command[2])
            if self._distance < 0:
                self._direction = -1
            else:
                self._direction = 1
            self._speed = self._distance/self._durationposition
            self.tOld = time.time()
            self._endTime = self._duration + time.time()
        elif command[0] == 'Stop':
            self.tOld = None
            self.init()
            pass

    def init(self):
        """
        Initialize properties
        :return:
        """
        self._movPos = 0.0
        self._speed = 0.0
        self._requestedPos = 0.0
        self._duration = 0.0
        self._distance = 0.0
        self._endTime = 0.0
        self._direction = 1

    def warpto(self, x=None):
        """
        Warp to home position
        :return:homePos
        """
        self._position = 0.0
        self.tOld = None


if __name__ == '__main__':
    import time

    def move(sled_obj, position, duration):
        # Move sled to a given position and print its current position and velocity
        print('Moving from {} to {}'.format(sled_obj.getposition()[0], position))
        sled_obj.move(position, duration)

        while not sled_obj.validate():
            print(sled_obj)

        print('Sled at {}'.format(sled_obj.getposition()[0]))
        print('Sled at position: {}'.format(sled_obj.at_position(position)))

    homePos = 0.0  # Home Position
    startPos = -0.20  # Home Position
    EndPos = 0.20
    movDistance = 0.40
    movDuration = 2.0
    movBackDuration = 3.0

    sled = Sled(dummy_mode=False, server='sled')
    sled.lights(False)  # Turn the lights OFF

    while not sled.at_position(homePos):
        print('Sled not at home position')

    try:
        if not sled.at_position(homePos):
            print('Sled not at home position')
            move(sled, homePos, movBackDuration)

        print('Initial sled position at {}'.format(sled.getposition()[0]))

        # Move sled to start position
        move(sled, startPos, movBackDuration)

        # Move sled to final position
        move(sled, EndPos, movDuration)

    except (TypeError, Exception, KeyboardInterrupt):
        print(TypeError)
    finally:
        sled.lights(True)  # Turn the lights ON
        sled.close()
        exit(0)

