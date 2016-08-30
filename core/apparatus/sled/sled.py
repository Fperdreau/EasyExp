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

__author__ = 'Florian Perdreau'
__copyright__ = '2016'
__license__ = 'GPL'


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

    def __init__(self, dummy_mode=False, server=False, port=3375):
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
        self.client = None
        self.positionClient = None
        self.port = port
        self.position = 0.0
        self.server = server
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
        self.client.goto(self.home)  # homing sled at -reference

    def connectPositionServer(self, server=None):
        """
        Connect to a First Principles server which returns the viewer position in the first marker position.
        Make sure this function is called after connectSledServer so that the fall back option is present.
        :param server:
        """
        # logging.debug("requested position server: " + str(server))
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

    def stop(self):
        """
        Stop the sled movement and stop the timer

        :return: void
        """
        self.client.sendCommand('{} stop'.format(self.moveType))
        duration = time.time() - self.timer
        self.timer = time.time()
        print('[{0}] Sled duration: {1} seconds'.format(__name__, duration))
        return duration

    def close(self):
        """
        Close connection with the Sled Client

        :return: void
        """
        # Return to home position
        self.move(self.home, self.mvt_back_duration)
        time.sleep(self.mvt_back_duration)

        # Switch lights on
        self.lights(True)

        # Close clients
        print("[{}] Closing Sled client".format(__name__))  # logger may not exist anymore
        try:
            self.client.stopStream()
        except Exception:
            raise Exception('[{}] Could not stop client stream')

        if hasattr(self, "positionClient") and hasattr(self.positionClient, "stopStream"):
            print("[{}] closing Position client".format(__name__))  # logger may not exist anymore
            try:
                self.positionClient.stopStream()
            except Exception:
                raise Exception('[{}] Could not stop positionClient stream')

        print('[{}] Stream successfully stopped'.format(__name__))

        self.client.sendCommand('Bye')
        self.client.__del__()

    def getposition(self, t=None, dt=None):
        """
        Get sled position
        :return: numpy matrix
        """
        pp = self.client.getPosition(t=t, dt=dt)
        self.position = np.array(pp).ravel().tolist()  # python has too many types
        return self.position

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
        print('[{}] !!! Sled running in dummy mode !!!'.format(__name__))

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
            self._speed = self._distance/self._duration
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
        :return:
        """
        self._position = 0.0
        self.tOld = None


if __name__ == '__main__':
    import time

    homePos = -0.30  # Home Position
    EndPos = 0.30
    movDistance = 0.60
    movDuration = 2.0
    movBackDuration = 3.0

    sled = Sled(status=True, server='sled')
    sled.lights(False)  # Turn the lights OFF

    sled.move(homePos, movBackDuration)
    time.sleep(movBackDuration)
    sled.getposition()
    print('Home Position - Sled position: {}'.format(sled.position[0]))

    sled.move(EndPos, movDuration)
    time.sleep(movDuration)
    sled.getposition()
    print('EndPosition - Sled position: {}'.format(sled.position[0]))

    sled.move(homePos, movBackDuration)
    time.sleep(movBackDuration)
    sled.getposition()
    print('Home Position: Sled position: {}'.format(sled.position[0]))

    sled.move(0.0, 1.5)
    time.sleep(1.5)
    sled.getposition()
    print('Center: Sled position: {}'.format(sled.position[0]))

    sled.lights(True)  # Turn the lights ON
    sled.close()
