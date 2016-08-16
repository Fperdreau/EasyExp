#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (C) 2015 Florian Perdreau, Radboud University Nijmegen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Imports
from os.path import isfile
from ...com.fpclient.fpclient import FpClient
import time
import math
import numpy as np
import pymouse


class OptoTrack(object):
    """
    Wrapper class for Optotrack
    """

    default_labels = 'origin'

    def __init__(self, name='test', freq=60.0, labels=None, origin=None, status=False, trackedhand={'origin'}, velocityThres=0.01,
                 timeWindow=0.010):
        """
        Constructor
        :param velocityThres: Velocity threshold
        :param timeWindow:
        :param name: file name
        :param labels: sensor labels
        :param status: if False, then runs in dummy mode
        :param trackedhand: the sensors to track
        :return:
        """
        self.originID = labels.index(origin) if (labels is not None and origin is not None) else 0
        self.status = status
        self.running = False
        self.prevPosition = None
        self.valid_time = None
        self.final_hand_position = False
        self.velocityThres = velocityThres

        # Sampling frequency
        self.freq = 1.0/freq
        self.freqInitTime = time.time()

        # Tracked sensor (only corresponding data will be recorded)
        self.trackedHand = trackedhand

        # Timers
        self.tOld = None
        self.dt = 0
        self.initTime = time.time()
        self.timeWindow = timeWindow

        # Arrays
        self.positions = {}
        self.sensors = {}

        # FPclient
        self.client = None

        # Data File
        self.file = None
        self.fileName = '{}_opto_{}.txt'.format(name, time.strftime('%d-%m-%Y_%H%M%S'))

        # Sensors name
        self.labels = labels if labels is not None else self.default_labels

    def setTrackeHand(self, hand):
        self.trackedHand = hand
        self.initTracked()

    def initTracked(self):
        """
        Initialize properties relative to tracked sensors
        :return:
        """
        for tracked in self.trackedHand:
            self.sensors[tracked] = Sensor(self, tracked, originID=self.originID)
        return True

    def distance(self, init, end):
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

    def connect(self):
        """
        Connection routine
        :return:
        """
        try:
            self.client.connect('optotrak')
            print '[Optotrack] Connection successful!'
            time.sleep(2)
            return True
        except Exception as e:
            print '[Optotrack] Connection failed: {}'.format(e)
            print '[Optotrack] Trying to close the socket'
            self.client.sock.close()
            time.sleep(5)  # Wait 2 seconds to make sure the socket is properly closed
            return False

    def init(self):
        """
        Inialization routine
        :return:
        """
        if self.status:
            try:
                self.client = FpClient()
            except Exception as e:
                raise '[Optotrack] Could not instantiate FpClient session: {}'.format(e)
        else:
            self.client = DummyOpto(self.labels)

        # Connect to the Optotrack
        connected = False
        attempt = 0
        while not connected and attempt <= 3:
            if attempt >= 1:
                print '[Optotrack] Connection Attempt # {}'.format(attempt)
            connected = self.connect()
            attempt += 1

        self.client.startStream()
        time.sleep(4)  # Add extra delays to ensure the connection is opened

        # Open hand data file
        self.openfile()

        # Write header
        self.writeheader()

        # Init and instantiate sensors
        self.initTracked()

    def quit(self):
        """
        Exit routine (close used socket and stop streaming)
        :return:
        """
        print('[Optotrack] Closing connection...')
        self.stop_recording() # Stop recording
        self.closefile()  # close data file
        self.client.close()  # Close connection to FPclient
        print('[Optotrack] Connection closed!')

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
            marker.getPosition()
            coordtowrite = '{} {}'.format(markers, self.position2Str(marker.position))
            markersCoord = ' '.join((markersCoord, coordtowrite))

        # collect some samples
        initTime = time.time()
        while time.time() - initTime < 0.100:
            self.get_position()

        self.sendMessage('SYNCTIME {}'.format(markersCoord))

    def stop_recording(self):
        """
        Stop recording data
        :return:
        """
        self.sendMessage('STOP_RECORDING')
        self.running = False

    def get_position(self):
        """
        Get current position
        :return:
        """
        for tracked in self.trackedHand:
            self.sensors[tracked].getPosition()

    def recordPosition(self):
        """
        Write position to a file
        :return:
        """
        if self.running:
            self.get_position()
            if (time.time() - self.freqInitTime) >= self.freq:
                # print ('elapsed: {} s'.format(time.time() - self.freqInitTime))
                self.freqInitTime = time.time()
                datatowrite = '{}'.format(time.time())
                for tracked in self.trackedHand:
                    coordtowrite = '{} {}'.format(tracked, self.position2Str(self.sensors[tracked].position))
                    datatowrite = ' '.join((datatowrite, coordtowrite))
                self.write(datatowrite)
                return True
            else:
                return False
        else:
            return False

    def start_trial(self, trial, param=None):
        """
        Start trial routine
        :param trial: trial number
        :return:
        """
        # Open file
        self.openfile()

        self.sendMessage('\r\n\r\nTRIALID {}'.format(trial))
        if param is not None:
            data = ''
            for prop, val in param.iteritems():
                parsedParams = '{} {}'.format(prop, val)
                data = ' '.join((data, parsedParams))
            self.sendMessage('\nTRIAL_PARAM {}'.format(data))

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

        self.sendMessage('\nTRIAL_END {} {}'.format(trial, trial_status))
        self.stop_recording()  # Stop recording
        self.closefile()  # Close data file

    def openfile(self):
        """
        Create the datafile and write the header
        :return:
        """
        try:
            self.file = open(self.fileName, 'ab', 0)
        except (IOError, TypeError):
            print "[Optotrack] Could not write into the user's datafile: {}".format(self.fileName)
            print "[Optotrack] Error: {}".format(IOError)
            raise

    def closefile(self):
        """
        Close data file
        :return:
        """
        if self.file is not None and not self.file.closed:
            self.file.close()

    def writeheader(self):
        """
        Write header into the data file
        :return:
        """
        if self.file is not None and not self.file.closed:
            self.write('############################')
            self.write('##  Optotrack recording')
            self.write('##  Date: {}'.format(time.strftime("%d-%m-%y")))
            self.write('##  Sampling Frequency: {} ms'.format(self.freq))
            self.write('##  Sensors: {}'.format(self.labels))
            self.write('##  Tracked: {}'.format(self.trackedHand))
            self.write('############################\r\n')
        else:
            print '[Optotrack] Could not write header'

    def sendMessage(self, msg):
        """
        Send an Event message and write it to the datafile
        :param msg:
        :return:
        """
        self.write('MSG {0:.4f} {1}'.format(time.time(), msg))

    def position2Str(self, position):
        """
        Convert position to string
        :param position:
        :return: string
        """
        converted = ' '.join(str(n) for n in position)
        return converted

    def write(self, datatowrite):
        """
        Write to the datafile
        :param datatowrite:
        :return:
        """
        if self.file is not None and not self.file.closed:
            try:
                self.file.write(datatowrite+'\r\n')
            except (IOError, TypeError):
                print "[Optotrack] Could not write into the user's datafile: {}".format(self.fileName)
                print "[Optotrack] Error: {}".format(IOError)
                raise
        else:
            print '[Optotrack] File has not been opened'


class Sensor(OptoTrack):
    """
    Instantiate tracked sensor
    """
    def __init__(self, parent, name='marker', originID=0):
        """
        Sensor constructor
        :param parent: Instance of Optotrak class
        :param name: Sensor's label
        :param originID: Index of origin marker
        :return:
        """
        super(Sensor, self).__init__()

        self.name = name
        self.originID = originID
        self.fileName = parent.fileName
        self.id = parent.labels.index(self.name)
        self.client = parent.client
        self.timeWindow = parent.timeWindow

        self.position = [False, False, False]
        self.velocity = 0.0
        self.history = None

        self.final_hand_position = False
        self.valid_time = None

        # Timer
        self.dt = 0.0
        self.tOld = None
        self.timeinterval = 0.010

    def update(self):
        """
        Update sensor's state
        :return:
        """
        self.getPosition()
        self.getHistory()
        self.getVelocity()

    def getPosition(self):
        """
        Get current position
        :return:
        """
        positions = self.client.getPosition()
        origin = np.asarray(positions[self.originID])
        this = np.asarray(positions[self.id])
        self.position = np.asarray(this[0] - origin[0])

        # Add position to history
        self.getHistory()
        return self.position

    def getHistory(self):
        if self.tOld is None:
            self.tOld = time.time()
            self.dt = 0.0
        else:
            self.dt = time.time() - self.tOld
            self.tOld = time.time()

        if self.dt >= self.timeinterval:
            if self.history is None:
                self.history = np.array(self.position)
            else:
                r = self.history.shape
                if len(r) == 1:
                    old = self.history
                    self.history = np.vstack((old, self.position))
                elif r[0] > 1:
                    old = self.history[1]
                    self.history = np.vstack((old, self.position))
            self.tOld = time.time()
        return self.history

    def getVelocity(self):
        """
        Get velocity
        :return:
        """
        if self.history is not None:
            r = self.history.shape
            if len(r) > 1 and r[0] > 1:
                distance = self.distance(self.history[1], self.history[0])
                self.velocity = distance/self.timeinterval
        return self.velocity

    def validposition(self, threshold_time=0.100):
        """
        validate sensor's position
        :return:
        """
        status = False
        self.getVelocity()
        self.final_hand_position = False
        if self.velocity < self.velocityThres:
            if self.valid_time is None:
                self.sendMessage('EVENT_START_VALIDATION {}'.format(self.name))
                status = 'validation'
                self.valid_time = time.time()

            elif time.time() - self.valid_time > threshold_time:
                self.final_hand_position = self.position
                datatowrite = self.position2Str(self.final_hand_position)
                self.sendMessage('EVENT_END_VALIDATION {} {}'.format(self.name, datatowrite))
                self.valid_time = None
                status = True
        else:
            # Restart the timer
            self.valid_time = None
        return status

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
        print '\n!!! [Optotrack] Runs in Dummy Mode !!!\n'

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


class checkPosition(object):
    """
    Get user response: validate hand position
    """
    def __init__(self, optotrack, marker, start_position, radius, duration):
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
                    print('Start checking')
                    self.responseChecking_start = time.time()
                    self.responseChecking = True
                else:
                    self.done = time.time() - self.responseChecking_start >= self.duration
                    if self.done:
                        print('Position validated')
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
        print self.velocity

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
    optotrak = OptoTrack('test', freq=500.0, velocityThres=0.010, timeWindow=0.050,
                         labels=('X-as', 'Marker_2', 'Y-as', 'origin', 'hand1', 'hand2'),
                         status=True, trackedhand={'hand1', 'hand2'})

    # Initialization and connection procedure
    optotrak.init()
    homeFromHand1 = np.array((0, 0.418, 0))  # distance of rail extremity (marker hand1) to sled center
    initHandPosition = optotrak.sensors['hand1'].getPosition() + homeFromHand1
    print 'Home position: {}'.format(initHandPosition)

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
    PositionChecker = checkPosition(optotrak, hand, initHandPosition, radiusIn, 0.100)

    init_time = time.time()
    status = False
    print 'Wait the hand at the initial position'
    optotrak.sendMessage('Wait the hand at the initial position')

    timeinit = time.time()
    while not status:
        recorded = optotrak.recordPosition()
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

    print 'The hand is at the initial position'
    optotrak.sendMessage('The hand is at the initial position')

    print 'Wait for the hand starting to move'
    optotrak.sendMessage('Wait for the hand starting to move')

    print 'Start reponse'
    optotrak.sendMessage('EVENT_RESPONSE_START')
    mvtDuration = None
    status = True
    while status or hand.validposition(threshold_time=0.050) is not True:
        recorded = optotrak.recordPosition()
        status = optotrak.sensors['hand2'].checkposition(initHandPosition, radiusOut)
        optotrak.sensors['hand2'].getPosition()
        optotrak.sensors['hand2'].getVelocity()
        if status is False and mvtDuration is None:
            print 'Movement started'
            mvtDuration = time.time()

        msg = 'Response: init: {} coord: {} | Velocity: {}'.format(initHandPosition, optotrak.sensors['hand2'].position,
                                                                   optotrak.sensors['hand2'].velocity)
        text = visual.TextStim(win, text=msg, pos=(0, 0))
        text.draw()
        win.flip()
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]: break

    print 'Got response'
    print 'Mvt Duration: {}'.format(round( (time.time()-mvtDuration)*1000))
    optotrak.sendMessage('EVENT_RESPONSE_END {}'.format(hand.position))

    # Stop
    optotrak.stop_trial(1)
    optotrak.quit()

    # Close window
    win.close()







