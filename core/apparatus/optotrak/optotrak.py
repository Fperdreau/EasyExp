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

# Imports
from __future__ import print_function

from os.path import isfile
import time
import math
import numpy as np
import pymouse

# FPClient
try:
    from ...com.fpclient.fpclient import FpClient
except ImportError as e:
    raise ImportError('Could not import FPClient, but FPClient is required to use OptoTrak class: {}'.format(e))

# Logger
import logging


class OptoTrak(object):
    """
    Wrapper class for Optotrack
    """

    default_labels = 'origin'
    user_file = 'sample.txt'
    dummy_mode = False

    def __init__(self, user_file='sample.txt', freq=60.0, labels=None, origin=None, dummy_mode=False, tracked={'origin'},
                 velocity_threshold=0.01, time_threshold=0.010, logger_label='root'):
        """
        Constructor
        :param velocity_threshold: Velocity threshold
        :param time_threshold:
        :param user_file: file name
        :param labels: sensor labels
        :param dummy_mode: if False, then runs in dummy mode
        :param tracked: the sensors to track
        :param logger_label: logger name
        :return:
        """
        self.logger = logging.getLogger(logger_label)
        self.originID = labels.index(origin) if (labels is not None and origin is not None) else 0
        self.dummy_mode = dummy_mode
        self.velocityThres = velocity_threshold
        self.timeWindow = time_threshold
        self.tracked = tracked

        # Sensors name
        self.labels = labels if labels is not None else self.default_labels

        self.running = False

        # Sampling frequency
        self.freq = 1.0/freq
        self.freqInitTime = time.time()

        # Tracked sensor (only corresponding data will be recorded)

        # Arrays
        self.positions = {}
        self.sensors = {}

        # Optotrak client (FPClient or dummy)
        self.client = None

        # Data File
        self.file = File(name=user_file)

    def connect(self):
        """
        Connection routine
        :return:
        """
        try:
            self.client.connect('optotrak')
            self.logger.info('[{}] Connection successful!'.format(__name__))
            time.sleep(2)
            return True
        except Exception as e:
            self.logger.critical('[{}] Connection failed: {}'.format(__name__, e))
            self.logger.warning('[{}] Trying to close the socket'.format(__name__))
            self.client.sock.close()
            time.sleep(5)  # Wait 2 seconds to make sure the socket is properly closed
            return False

    def init(self):
        """
        Inialization routine
        :return:
        """
        if not self.dummy_mode:
            try:
                self.client = FpClient()
            except Exception as e:
                msg = Exception('[{}] Could not instantiate FpClient: {}'.format(__name__, e))
                self.logger.fatal(msg)
                raise msg
        else:
            self.client = DummyOpto(self.labels)

        # Connect to the Optotrack
        connected = False
        attempt = 0
        while not connected and attempt <= 3:
            if attempt >= 1:
                self.logger.info('[{}] Connection Attempt # {}'.format(attempt, __name__))
            connected = self.connect()
            attempt += 1

        self.client.startStream()
        time.sleep(4)  # Add extra delays to ensure the connection is opened

        # Open hand data file
        self.file.open()

        # Write header
        self.__writeheader()

        # Init and instantiate sensors
        self.init_tracked()

    def close(self):
        """
        Exit routine (close used socket and stop streaming)
        :return:
        """
        self.logger.info('[{}] Closing connection...'.format(__name__))
        self.stop_recording() # Stop recording
        self.file.close()  # close data file
        self.client.close()  # Close connection to FPclient
        self.logger.info('[{}] Connection closed!'.format(__name__))

    def start_recording(self):
        """
        Start recording data
        :return:
        """
        self.running = True
        time.sleep(0.100)

        # Record all the markers position for further information
        markersCoord = ''
        for markers in self.labels:
            marker = Sensor(self, markers)
            coordtowrite = '{} {}'.format(markers, self.position_to_str(marker.position))
            markersCoord = ' '.join((markersCoord, coordtowrite))

        # collect some samples
        init_time = time.time()
        while time.time() - init_time < 0.100:
            self.get_position()

        self.send_message('SYNCTIME {}'.format(markersCoord))

    def stop_recording(self):
        """
        Stop recording data
        :return:
        """
        self.send_message('STOP_RECORDING')
        self.running = False

    def init_tracked(self):
        """
        Init tracked sensors
        :return:
        """
        print(self.tracked)
        for sensor in self.tracked:
            print("Adding {}".format(sensor))
            self.add_sensor(sensor)

    def add_sensor(self, sensor_label):
        """
        Set tracker sensor
        :param sensor_label:
        :return:
        """
        if sensor_label not in self.sensors:
            self.sensors[sensor_label] = Sensor(self, sensor_label, origin_id=self.originID)

    def del_sensor(self, sensor_label):
        """
        Remove sensor from tracked list
        :param sensor_label: sensor's label
        :type sensor_label: str
        :return:
        """
        if sensor_label in self.tracked:
            del self.sensors[sensor_label]

    def get_position(self):
        """
        Get current position
        :return:
        """
        for tracked in self.tracked:
            self.sensors[tracked].get_position()

    def update(self):
        """
        Update sensor information
        :return:
        """
        for tracked in self.tracked:
            self.sensors[tracked].update()

    def record(self):
        """
        Write position to a file
        :return:
        """
        if self.running:
            if (time.time() - self.freqInitTime) >= self.freq:
                # print ('elapsed: {} s'.format(time.time() - self.freqInitTime))
                self.freqInitTime = time.time()
                datatowrite = '{}'.format(time.time())
                for tracked in self.tracked:
                    coordtowrite = '{} {}'.format(tracked, self.position_to_str(self.sensors[tracked].position))
                    datatowrite = ' '.join((datatowrite, coordtowrite))
                self.file.write(datatowrite)
                return True
            else:
                return False
        else:
            return False

    def start_trial(self, trial, param=None):
        """
        Start trial routine
        :param trial: trial number
        :type trial: int
        :param param: Trial parameters
        :type param: dict
        :return:
        """
        # Open file
        self.file.open()

        self.send_message('\r\n\r\nTRIALID {}'.format(trial))
        if param is not None:
            data = ''
            for prop, val in param.iteritems():
                parsed_param = '{} {}'.format(prop, val)
                data = ' '.join((data, parsed_param))
            self.send_message('\nTRIAL_PARAM {}'.format(data))

        # Start recording
        self.start_recording()

    def stop_trial(self, trial, valid=True):
        """
        Stop trial routine
        :param trial: trial id
        :param valid: boolean (valid or invalid trial)
        :return:
        """
        if valid:
            trial_status = 'VALID'
        else:
            trial_status = 'INVALID'

        self.send_message('\nTRIAL_END {} {}'.format(trial, trial_status))
        self.stop_recording()  # Stop recording
        self.file.close()  # Close data file

    def __writeheader(self):
        """
        Write header into the data file
        :return:
        """
        header = '############################\r\n' \
                 '# Optotrak data file\r\n' \
                 '# Date: {}\r\n' \
                 '# Sampling Frequency: {} ms\r\n' \
                 '# Sensors: {}\r\n' \
                 '# Tracked: {}\r\n' \
                 '############################\r\n'.format(time.strftime("%d-%m-%y"), self.freq,
                                                           ', '.join(self.labels), ', '.join(self.tracked))
        self.file.write(header)

    def send_message(self, message):
        """
        Send an Event message and write it to the datafile
        :param message:
        :return:
        """
        self.file.write('MSG {0:.4f} {1}'.format(time.time(), message))

    @staticmethod
    def position_to_str(position):
        """
        Convert position to string
        :param position:
        :return: string
        """
        converted = ' '.join(str(n) for n in position)
        return converted

    @staticmethod
    def distance(init, end):
        """
        Compute spherical distance between two given points
        :param init:
        :param end:
        :return:
        """
        x_diff = end[0] - init[0]
        y_diff = end[1] - init[1]
        z_diff = end[2] - init[2]
        distance = math.sqrt(x_diff**2+y_diff**2+z_diff**2)
        return distance


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
        self.id = None
        self.handler = None

    def open(self):
        """
        Create the datafile and write the header
        :return:
        """
        try:
            self.handler = open(self.name, 'ab', 0)
        except (IOError, TypeError) as e:
            msg = ("[Optotrack] Could not write into the user's datafile: {}".format(self.name, e))
            logging.critical(msg)
            raise msg

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
                self.handler.write(datatowrite + '\r\n')
            except (IOError, TypeError) as e:
                msg = ("[{}] Could not write into the user's datafile ({}): {}".format(__name__, self.name, e))
                logging.critical(msg)
                raise msg
        else:
            logging.warning('[{}] File has not been opened'.format(__name__))


class Sensor(OptoTrak):
    """
    Instantiate tracked sensor
    """

    def __init__(self, parent, name='marker', origin_id=0):
        """
        Sensor constructor
        :param parent: Instance of Optotrak class
        :type parent: OptoTrak
        :param name: Sensor's label
        :type name: str
        :param origin_id Index of origin marker
        :type origin_id: int
        :return:
        """
        super(Sensor, self).__init__()

        self.name = name
        self.originID = origin_id
        self.fileName = parent.user_file
        self.id = parent.labels.index(self.name)
        self.client = parent.client
        self.timeWindow = parent.timeWindow

        self.history = None
        self.final_hand_position = False
        self.valid_time = None

        # Timer
        self.dt = 0.0
        self.tOld = None
        self.time_interval = 0.010

    def update(self):
        """
        Update sensor's state
        :return:
        """
        self.get_position()
        self.get_velocity()

    @property
    def position(self):
        """
        Sensor's position
        :return:
        """
        positions = self.client.getPosition()
        origin = np.asarray(positions[self.originID])
        this = np.asarray(positions[self.id])
        position = np.asarray(this[0])

        # Add position to history
        self.add_history(position)
        return position

    def get_position(self):
        """
        Get current position
        :return:
        """
        return self.position

    def add_history(self, position):
        """
        Add new position to sensor's position history in order to compute statistics
        :return:
        """
        if self.tOld is None:
            self.tOld = time.time()
            self.dt = 0.0
        else:
            self.dt = time.time() - self.tOld
            self.tOld = time.time()

        if self.dt >= self.time_interval:
            if self.history is None:
                self.history = np.array(position)
            else:
                r = self.history.shape
                if len(r) == 1:
                    old = self.history
                    self.history = np.vstack((old, position))
                elif r[0] > 1:
                    old = self.history[1]
                    self.history = np.vstack((old, position))
            self.tOld = time.time()
        return self.history

    @property
    def velocity(self):
        """
        Get velocity
        :return:
        """
        if self.history is not None:
            r = self.history.shape
            if len(r) > 1 and r[0] > 1:
                distance = self.distance(self.history[1], self.history[0])
                velocity = distance/self.time_interval
                return velocity
            else:
                return 0.0
        else:
            return 0.0

    def get_velocity(self):
        """
        Velocity getter
        :return: sensor's velocity
        """
        return self.velocity

    def validposition(self, threshold_time=0.100):
        """
        validate sensor's position
        :param threshold_time: minimum period during which the sensor must stay within the same spatial region in order
        to be considered as not moving
        :rtype: bool
        """
        validated = False
        self.final_hand_position = False
        if self.velocity < self.velocityThres:
            if self.valid_time is None:
                self.send_message('EVENT_START_VALIDATION {}'.format(self.name))
                self.valid_time = time.time()

            elif time.time() - self.valid_time > threshold_time:
                self.final_hand_position = self.position
                datatowrite = self.position_to_str(self.final_hand_position)
                self.send_message('EVENT_END_VALIDATION {} {}'.format(self.name, datatowrite))
                self.valid_time = None
                validated = True
        else:
            # Restart the timer
            self.valid_time = None
        return validated

    def checkposition(self, (x, y, z), radius):
        """
        Check that the tracked hands are located within a range from a given position
        :param radius:
        :return:
        """
        ref_position = np.array((x, y, z))
        distance = self.distance(ref_position, self.position)
        return distance <= radius


class DummyOpto(object):
    """
    Dummy Mode of the optotrack
    Simulate tracked position with the mouse
    """

    def __init__(self, labels):
        self.nbSensors = len(labels)
        print('[{}] Runs in Dummy Mode !!!'.format(__name__))

    def connect(self, type):
        return True

    def close(self):
        pass

    def startStream(self):
        pass

    def stopStream(self):
        pass

    def getPosition(self):
        m = pymouse.PyMouse()
        try:
            x, y = m.position()
        except:
            from psychopy import event
            mouse = event.Mouse()
            x, y = mouse.getPos()
        z = 0

        # Return coordinates
        coord = []
        for s in range(self.nbSensors):
            if s <= 3:
                coord.append([0, 0, 0])
            else:
                coord.append([x, y, z])

        return np.matrix(coord)


class CheckPosition(object):
    """
    Position checker: control that a sensor is located within a defined region for a particular amount of time
    (optional)
    """

    def __init__(self, optotrack, marker, start_position, radius, duration):
        """

        :param optotrack: Optotrak instance
        :type optotrack: OptoTrak
        :param marker: marker name
        :param start_position: reference position
        :type start_position: ndarray
        :param radius: distance between sensor position and reference position
        :type radius: float
        :param duration: period (in seconds) during with the sensor must stay within the defined region to be considered
         as stable
        :type duration: float
        """
        self.tracker = optotrack
        self.marker = marker
        self.duration = duration
        self.radius = radius
        self.start_position = start_position
        self.responseChecking = False
        self.done = False
        self.responseChecking_start = time.time()

    def validateposition(self):
        """
        Check if the sensor stays within the same spatial region
        """
        if not self.done:
            status = self.marker.checkposition(self.start_position, self.radius)
            
            if status:
                if not self.responseChecking:
                    self.tracker.logger.info('[{}] Start checking'.format(__name__))
                    self.responseChecking_start = time.time()
                    self.responseChecking = True
                else:
                    self.done = time.time() - self.responseChecking_start >= self.duration
                    if self.done:
                        self.tracker.logger.info('[{}]Position validated'.format(__name__))
            else:
                self.responseChecking = False
        return self.done


class Group(object):
    """
    Wrapper class that tracks a set of markers as a single unit (i.e. rigid body)
    Methods:
    init() = instantiate the group's sensors
    getPosition() = get the average position of the available sensors
    getVelocity() = get the average velocity of the available sensors
    """

    def __init__(self, tracker, labels):
        """
        Constructor
        :param tracker: object of class Optotrack
        :param labels: dictionary of sensors' labels included in this group
        :return:
        """
        self.tracker = tracker
        self.labels = labels
        self.sensors = self.init()

        self.position = np.array([])
        self.velocity = 0
        self.valid_time = None
        self.final_hand_position = False

    def init(self):
        """
        Instantiate the group's sensors
        :return:
        """
        sensors = {}
        for sensor in self.labels:
            sensors[sensor] = Sensor(self.tracker, sensor)
        return sensors

    def getPosition(self):
        """
        Get the group's sensors position
        :return: return the average position of available sensors
        """
        self.position = np.array([0, 0, 0])
        s = 0
        for sensor in self.labels:
            self.sensors[sensor].getPosition()
            pos = self.sensors[sensor].position
            if not np.isnan(np.sum(pos)):
                self.position = np.vstack((self.position, pos))
                s += 1
        if s > 1:
            self.position = np.delete(self.position, 0, 0)
            self.position = np.mean(self.position, axis=0)
        elif s == 1:
            self.position = self.position[1, :]
        elif s == 0:
            self.position = np.array([0, 0, 0])

        return self.position
            
    def getVelocity(self):
        """
        Get group's sensors velocity.
        :return: return the average velocity of available sensors
        """
        velocity = np.array([])
        s = 0
        for sensor in self.labels:
            self.sensors[sensor].getPosition()
            self.sensors[sensor].getVelocity()
            vel = self.sensors[sensor].velocity
            if not np.isnan(vel):
                velocity = np.hstack((velocity, vel))
                s += 1
        velocity = np.mean(velocity)
        if s > 0 and not np.isnan(velocity):
            self.velocity = velocity

    def checkposition(self, (x, y, z), radius):
        """
        Check that the tracked hands are located within a range from a given position
        :param radius:
        :return:
        """
        self.getPosition()
        ref_position = np.array((x, y, z))
        distance = self.tracker.distance(ref_position, self.position)
        status = distance <= radius
        return status

    def validposition(self, threshold_time=0.100):
        """
        validate final hand position
        :param threshold_time
        :return:
        """

        status = False
        self.getPosition()
        self.getVelocity()
        self.final_hand_position = False
        if self.velocity < self.tracker.velocityThres:
            if self.valid_time is None:
                self.tracker.sendMessage('EVENT_START_VALIDATION')
                status = 'validation'
                self.valid_time = time.time()

            elif time.time() - self.valid_time > threshold_time:
                self.final_hand_position = self.position
                datatowrite = self.tracker.position2Str(self.final_hand_position)
                self.tracker.sendMessage('EVENT_END_VALIDATION {}'.format(datatowrite))
                self.valid_time = None
                status = True
        else:
            # Restart the timer
            self.valid_time = None
        return status


if __name__ == '__main__':
    import time
    import numpy as np
    from psychopy import visual
    import pygame

    radiusIn = .03  # in meters
    radiusOut = .03

    # Create optotrack instance
    optotrak = OptoTrak('test', freq=500.0, velocity_threshold=0.010, time_threshold=0.050,
                        labels=('X-as', 'Marker_2', 'Y-as', 'origin', 'hand1', 'hand2'),
                        dummy_mode=True, tracked={'hand1', 'hand2'})

    # Initialization and connection procedure
    optotrak.init()
    homeFromHand1 = np.array((0, 0.418, 0))  # distance of rail extremity (marker hand1) to sled center
    initHandPosition = optotrak.sensors['hand1'].getPosition() + homeFromHand1
    print('Home position: {}'.format(initHandPosition))

    # Open window
    win = visual.Window(
        size=(1400, 525),
        monitor='TestMonitor',
        color=(0, 0, 0),
        units='norm',
        winType='pygame',
        pos=(0, 0),
        waitBlanking=True,
        fullscr=False)
    win.setMouseVisible(False)

    # Do some tests
    optotrak.start_trial(1)
    hand = optotrak.sensors['hand2']
    PositionChecker = CheckPosition(optotrak, hand, initHandPosition, radiusIn, 0.100)

    init_time = time.time()
    status = False
    print('Wait the hand at the initial position')
    optotrak.send_message('Wait the hand at the initial position')

    timeinit = time.time()
    while not status:
        recorded = optotrak.record()
        status = PositionChecker.validateposition()
        optotrak.sensors['hand2'].getPosition()
        optotrak.sensors['hand2'].getVelocity()
        hand_position = optotrak.sensors['hand2'].position
        hand_to_center = -(hand_position[1] - initHandPosition[1])

        msg = '[Start] init: {0} coord: {1} | ' \
              'distance: {2:1.2f} ' \
              'Velocity: {3:1.2f}'.format(initHandPosition, optotrak.sensors['hand2'].position, hand_to_center,
                                          optotrak.sensors['hand2'].velocity)

        text = visual.TextStim(win, text=msg, pos=(0, 0))
        text.draw()
        win.flip()
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]: break

    print('The hand is at the initial position')
    optotrak.send_message('The hand is at the initial position')

    print('Wait for the hand starting to move')
    optotrak.send_message('Wait for the hand starting to move')

    print('Start reponse')
    optotrak.send_message('EVENT_RESPONSE_START')
    mvtDuration = None
    status = True
    while status or hand.validposition(threshold_time=0.050) is not True:
        recorded = optotrak.record()
        status = optotrak.sensors['hand2'].checkposition(initHandPosition, radiusOut)
        optotrak.sensors['hand2'].getPosition()
        optotrak.sensors['hand2'].getVelocity()
        if status is False and mvtDuration is None:
            print('Movement started')
            mvtDuration = time.time()

        msg = 'Response: init: {} coord: {} | Velocity: {}'.format(initHandPosition, optotrak.sensors['hand2'].position,
                                                                   optotrak.sensors['hand2'].velocity)
        text = visual.TextStim(win, text=msg, pos=(0, 0))
        text.draw()
        win.flip()
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]: break

    print('Got response')
    print('Mvt Duration: {}'.format(round((time.time() - mvtDuration) * 1000)))
    optotrak.send_message('EVENT_RESPONSE_END {}'.format(hand.position))

    # Stop
    optotrak.stop_trial(1)
    optotrak.close()

    # Close window
    win.close()







