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

from __future__ import print_function

"""
Eyetracker is a wrapper class handling routines of the SR-Research(c) Eyelink.
It allows custom settings and custom calibrations. It has been designed so that the calibration procedure can be done
whatever the user uses a Pygame/Psychopy window or a Qt Application. To do so, the Eyetracker wrapper calls on external
dependencies:
- /display/display_psychopy: includes a modified version of the EyeLinkCoreGraphicsPsychopy class (child of
pylink.EyeLinkCustomDisplay)
- /display/display_pygame: includes DisplayPygame class (child of pylink.EyeLinkCustomDisplay)
- /display/qeyelink: includes QEyelink class (Wilbert van Ham (c)) (child of QtGui.QWidget and
 pylink.EyeLinkCustomDisplay)
"""

#  @todo : Improve and secure access to Eye instances (stored in EyeTracker.eyes dictionary)

try:
    from pylink import *
except ImportError as e:
    raise ImportError('[{}] EyeTracker wrapper class requires pylink (Eyelink) module to work: {}'.format(__name__, e))

from pygame import *
import time
import gc
import math
import random
import logging
import numpy as np

__version__ = '1.3.1'


def deg2pix(angle, direction=1, distance=550, screen_res=(800, 600), screen_size=(400, 300)):
    """
    Convert visual angle to pixels or pixels to visual angle.
    Parameters
    ----------
    :param angle: size to convert
    :type angle: float
    :param direction: direction of the conversion (1: Visual angle to
     pixels; 2= pixels to visual angle).
    :type direction: int
    :param distance: distance eye-screen in mm
    :type distance: int
    :param screen_res: screen resolution (width, height) in pixels
    :type screen_res: tuple
    :param screen_size: screen dimension (width, height) in mm
    :type screen_size: tuple

    Returns
    -------
    :return: converted size in pixels or visual angles [width, height].
    :rtype: tuple
    """

    widthscr, heightscr = [float(i) for i in screen_size]
    widthres, heightres = [float(i) for i in screen_res]

    if direction == 1:
        wdth = round(math.tan(deg2rad(angle/2))*2*distance*(widthres/widthscr))
        hght = round(math.tan(deg2rad(angle/2))*2*distance*(heightres/heightscr))
    else:
        wdth = rad2deg(math.atan(((angle/2)/(distance*(widthres/widthscr)))))*2
        hght = rad2deg(math.atan(((angle/2)/(distance*(heightres/heightscr)))))*2

    return [wdth, hght]


def deg2rad(angle):
    """
    Convert degrees to radians
    :param angle: angle to convert (in degree)
    :type angle: float

    :return: converted angle in radians
    """
    return float(angle*(math.pi/180))


def rad2deg(angle):
    """
    Convert radians to degrees
    :param angle: angle to convert (in radians)
    :type angle: float

    :return: converted angle in degrees
    """
    return float(angle/(math.pi/180))


# Constant
LEFT_EYE = 0
RIGHT_EYE = 1
BINOCULAR = 2
MOUSE = 3


class EyeTracker(object):
    """
    EyeTracker Class: handles attributes and routines for controlling the EyeLink
    """
    eye_list = ['LEFT_EYE', 'RIGHT_EYE', 'BINOCULAR', 'MOUSE']  # Used by eyeAvailable
    allowed_sprate = (250, 500, 1000, 2000)  # Allowed sampling rates
    user_file = None
    dummy_mode = False

    def __init__(self, link='10.0.0.20', dummy_mode=False, user_file='X', sprate=1000, thresvel=35, thresacc=9500, illumi=2, caltype='H3',
                 dodrift=False, trackedeye='RIGHT', display_type='pygame', ptw=None, bgcol=(127, 127, 127), distance=550,
                 resolution=(800, 600), winsize=(800, 600), inner_tgcol=(127, 127, 127), outer_tgcol=(255, 255, 255),
                 targetsize_out=1.5, targetsize_in=0.5):

        """
        EyeTracker constructor
        :param string link: IP address of the Eyelink
        :param bool dummy_mode: DummyMode (Eye is simulated by the mouse)
        :param str user_file: full path to destination edf file (e.g.: /full/path/to/edf_file * note: without extension)
        :param int sprate: Sampling rate (in Hz)
        :param int thresvel: Saccade velocity threshold
        :param int thresacc: Saccade acceleration threshold
        :param int illumi: Illumination of the infrared (1:100% 2:75% 3:50%)
        :param str caltype: Calibration type (HV5, ...)
        :param bool dodrift: Drift correction
        :param str trackedeye: Tracked eye ('LEFT','RIGHT','BINOCULAR')
        :param str display_type:
        :param ptw: Windows pointer
        :param tuple bgcol: Background color
        :param int distance: Distance eye-screen
        :param tuple resolution: screen's resolution (in pixels)
        :param tuple winsize: Screen's size (in mm)
        :param tuple inner_tgcol: inner target color
        :param tuple outer_tgcol: outer target color
        :param float targetsize_out: outer target size
        :param float targetsize_in: inner target size
        """
        self.el = None
        self.__logger = logging.getLogger('EasyExp')

        # File information
        # ================
        self.user_file = user_file  # EDF file name stored on the Experiment host

        # Check frequency sampling
        if sprate not in self.allowed_sprate:
            raise AttributeError('This sample rate is not supported. it must be one of {0}'.format(
                ', '.join(self.allowed_sprate)))

        # Eyetracker settings
        # ===================
        self.link = link  # IP address of the Eyelink
        self.dummy_mode = dummy_mode  # DummyMode (Eye is simulated by the mouse)
        self.sprate = sprate  # Sampling rate (in Hz)
        self.thresvel = thresvel  # Saccade velocity threshold
        self.thresacc = thresacc  # Saccade acceleration threshold
        self.illumi = illumi  # Illumination of the infrared (1:100% 2:75% 3:50%)
        self.dodrift = dodrift  # Drift correction
        self.trackedeye = trackedeye  # Tracked eye

        self.status = None
        self.vs = None  # EyeLink version string
        self.softvs = None  # software version
        self.recording = False  # Recording status
        self.trial = None  # Current trial ID
        self.eye = None

        # Connect to Eye Tracker
        # ======================
        self.connect()

        # Data file
        # =========
        self.file = EDFfile(self, self.user_file)

        # Display options
        # ===============
        self.__display = None
        self.graphics = {
            'display_type': display_type,
            'distance': distance,
            'resolution': resolution,
            'winsize': winsize,
            'bgcol': bgcol,
            'inner_tgcol': inner_tgcol,
            'outer_tgcol': outer_tgcol,
            'targetsize_in': targetsize_in,
            'targetsize_out': targetsize_out
        }

        if ptw is not None:
            self.set_display(ptw)

        # Calibration
        # ===========
        self.caltype = caltype
        self.calibration = None
        self.set_calibration()

    @property
    def display(self):
        return self.__display

    def set_display(self, ptw):
        """
        Set display
        :param ptw:
        :return:
        """
        if self.__display is None:
            self.__display = Display(self.el, ptw=ptw, **self.graphics)

    def set_calibration(self):
        """
        Set calibration
        :return:
        """
        if self.display is None:
            self.__logger.warning('A window pointer must be specified before instantiating Calibration by calling '
                                  'EyeTracker.set_display(ptw)')
        else:
            if self.calibration is None:
                self.calibration = Calibration(self, screen=self.display, cal_type=self.caltype)

    def unset_calibration(self):
        """
        Unset calibration instance
        :return:
        """
        del self.calibration
        self.calibration = None

    def unset_display(self):
        del self.__display
        self.__display = None

    def connect(self):
        """
        Connect to eyetracker or to dummy tracker
        :return:
        """
        if not self.dummy_mode and self.link is not None:
            self.__logger.info('[{0}] Connecting to the EyeLink at {1}'.format(__name__, self.link))
            try:
                self.el = EyeLink(self.link)
                self.__logger.info('[{0}] Connection successful!'.format(__name__))
            except RuntimeError as e:
                msg = "[{0}] Connection - Unexpected error: {1}".format(__name__, e)
                self.__logger.critical(msg)
                raise RuntimeError(msg)
        else:
            self.el = DummyMode()

    def send_command(self, cmd):
        """
            Sends a command to the eyelink
            :param cmd: command to send (must be a string)
            """
        try:
            self.el.sendCommand(cmd)
            error = self.el.commandResult()
            if error != 0:
                msg = ('[{0}] Command ({1}) could not be sent to eyetracker: {2}'.format(__name__, cmd, error))
                self.__logger.critical(msg)
                raise RuntimeError(msg)
        except RuntimeError as error:
            msg = ('[{0}] Command ({1}) could not be sent to eyetracker: {2}'.format(__name__, cmd, error))
            self.__logger.critical(msg)
            raise RuntimeError(msg)

    def send_message(self, message):
        """
        Sends a message to the eyelink
        :param message: message to send
        :type message: str
        """
        self.el.sendMessage(message)

    def run(self):
        """
        Startup routine
        """
        self.__logger.info('[{}] Eyetracker is starting up...'.format(__name__))
        self.el.setOfflineMode()
        self.getconnectionstatus()
        self.setup()
        self.file.open()
        self.__logger.info('[{}] Eyetracker successfully started'.format(__name__))

    def getconnectionstatus(self, verbose=False):
        """
        Check if the EyeLink is connected
        :param verbose: Do we allow warning messages?
        """
        self.status = self.el.isConnected()
        msg = 'unknown'
        if self.status == -1:
            msg = 'dummymode'
        elif self.status == 0:
            msg = 'not connected'
        elif self.status == 1:
            msg = 'connected'
        else:
            self.__logger.error('[{0}] The eyetracker retrieved an unknown status: {1}'.format(__name__, self.status))
            self.close()
        self.status = {self.status, msg}
        self.__logger.info('[{0}] Eyelink Status: {1}'.format(__name__, self.status))

    def getStatus(self):
        """
        Return the status of the connection to the eye tracker
        """
        if self.el.breakPressed():
            return "ABORT_EXPT"
        if self.el.escapePressed():
            return "SKIP_TRIAL"
        if self.el.isRecording() == 0:
            return "RECORDING"
        if self.el.isConnected():
            return "ONLINE"
        else:
            return "OFFLINE"

    def setup(self):
        """
        Setup routine
        """
        self.__logger.info('[{}] Eye tracker setup...'.format(__name__))
        self.setup_tracker()
        self.setup_filters()

    def setup_tracker(self):
        """
        Setup eye tracker
        """
        # Get tracker version
        self.softvs = 0
        self.vs = self.el.getTrackerVersion()

        self.__logger.info('[{0}] Eyelink version: {1}'.format(__name__, self.vs))
        if self.vs >= 3:
            tvstr = self.el.getTrackerVersionString()
            vindex = tvstr.find("EYELINK CL")
            self.softvs = int(float(tvstr[(vindex + len("EYELINK CL")):].strip()))

            self.send_command("enable_search_limits=YES")
            self.send_command("track_search_limits=YES")
            self.send_command("autothreshold_click=YES")
            self.send_command("autothreshold_repeat=YES")
            self.send_command("enable_camera_position_detect=YES")
            self.send_command('sample_rate = %d' % self.sprate)

        if self.vs >= 2:
            self.send_command("select_parser_configuration 0")
            if self.vs == 2:  # turn off scenelink camera stuff
                self.send_command("scene_camera_gazemap = NO")
        else:
            self.send_command("saccade_velocity_threshold = %d" % self.thresvel)
            self.send_command("saccade_acceleration_threshold = %d" % self.thresacc)

    def setup_filters(self):
        """
        Setup event and data filters
        :return:
        """
        # set EDF file contents
        self.send_command("file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON")
        if self.softvs >= 4:
            self.send_command("file_sample_data  = LEFT,RIGHT,GAZE,AREA,GAZERES,STATUS,HTARGET")
        else:
            self.send_command("file_sample_data  = LEFT,RIGHT,GAZE,AREA,GAZERES,STATUS")

        # set link data (used for gaze cursor)
        self.send_command("link_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON")
        if self.softvs >= 4:
            self.send_command("link_sample_data  = LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,HTARGET")
        else:
            self.send_command("link_sample_data  = LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS")

        self.send_command("button_function 5 'accept_target_fixation'")

    def get_eye_used(self):
        """
        Return the eye used 'left' or 'right'
        :return self.trackedeye: id of tracked eye(s) ('left' or 'right')
        """
        eu = self.el.eyeAvailable()
        if eu > 4:
            eu = 0
        self.trackedeye = self.eye_list[eu] if eu >= 0 else None

        if eu == RIGHT_EYE:
            self.el.sendMessage("EYE_USED 1 RIGHT")
        elif eu == LEFT_EYE or eu == BINOCULAR:
            self.el.sendMessage("EYE_USED 0 LEFT")
        elif eu == MOUSE:
            self.el.sendMessage("EYE_USED 0 LEFT")
        else:
            self.__logger.warning("[{}] Error in getting the eye information!".format(__name__))
            return TRIAL_ERROR
        return self.trackedeye

    def start_trial(self, trial, param=None):
        """
        Start trial routine
        :param trial: trial number
        :type trial: int
        :param param: Trial parameters
        :type param: dict
        :return:
        """
        self.trial = trial
        self.send_command('record_status_message "TRIAL %d"' % self.trial)
        self.send_command('set_idle_mode')
        self.send_command('clear_screen %d' % 0)  # clear tracker display and draw box at center

        self.el.sendMessage('TRIALID %d' % self.trial)
        if param is not None:
            data = ''
            for prop, val in param.iteritems():
                parsed_param = '{} {}'.format(prop, val)
                data = ' '.join((data, parsed_param))
            self.el.sendMessage('TRIAL_PARAM {}'.format(data))

        # Start recording the eye and collect some data
        self.start_recording()

    def stop_trial(self, trial_id, valid=True):
        """
        Routine running at the end of a trial
        :param trial_id: trial unique id
        :type trial_id: int
        :param valid: valid (True) or invalid (False) trial
        :type valid: bool
        """
        valid = 'VALID' if valid else 'INVALID'
        self.send_message('\nTRIAL_OK {} {}'.format(trial_id, valid))

        self.stop_recording()

    def start_recording(self, w_sample=1, w_event=1, s_sample=1, s_event=1):
        """
        Start recording the tracked eye and tests if it worked
        :param s_event: 1: write sample to EDF file
        :param s_sample: 1: writes events to EDF file
        :param w_event: 1: sends sample through link
        :param w_sample: 1: send events through link
        :return:
        """
        try:
            error = self.el.startRecording(w_sample, w_event, s_sample, s_event)
        except Exception as e:
            self.__logger.critical(e)
            raise e

        if error:
            return error
        gc.disable()

        # Begin the real time mode (Windows only)
        # @todo: an error occurs when running on Linux. This issue has been previously reported. Using the new version
        # of pylink (version 1.9) should fix it. For more information,
        # see https://www.sr-support.com/showthread.php?4106-pylink-beginRealTimeMode()-freezes-and-some-other-issues-
        # (Ubuntu-14-04-64-bit)&highlight=opensesame
        # To start the real time mode, uncomment the following line:
        # beginRealTimeMode(100)

        self.el.sendMessage('SYNCTIME')

        # Check for data availability
        if not self.el.waitForBlockStart(100, 1, 0):
            self.__logger.critical("[{}] ERROR: No link samples received!".format(__name__))
            return "ABORT_EXPT"

        # Get tracked eye and create Eye instance
        self.set_eye()

    def set_eye(self):
        """
        Set Eye object
        :return:
        """
        self.trackedeye = self.get_eye_used()
        self.eye = Eye(self, self.trackedeye)

    def stop_recording(self):
        """
        Stop recording instruction
        :return:
        """
        self.el.stopRecording()
        endRealTimeMode()
        pumpDelay(100)

    def close(self):
        """
        Close routine: shutdown the EyeLink, close data file and receive data file
        """
        self.__logger.info('[{}] Closing Eyetracker ...'.format(__name__))
        if self.el is not None:
            # File transfer and cleanup!
            self.el.setOfflineMode()
            msecDelay(500)

            # Close and retrieve file
            self.file.close()

            # Close connection
            try:
                self.el.close()
                self.__logger.info("[{}] Connection closed successfully".format(__name__))
            except Exception as e:
                self.__logger.warning(e)
                raise Exception('[{}] Could not close connection'.format(__name__))
        else:
            msg = "[{}] Eyelink not available, not closed properly".format(__name__)
            self.__logger.warning(msg)
            raise Exception(msg)

    @property
    def logger(self):
        """
        Return Logging instance
        :return:
        """
        return self.__logger

    def calibrate(self, ptw=None, custom=None, drift=None):
        """
        Perform eye-tracker calibration and drift correction
        This method is used for implementing eye-tracker calibration within a multi-threaded framework.
        :param ptw: window pointer
        :param custom: custom calibration settings (if None, then use standard calibration):
            for example: dict(x=[], y=[], ctype='HV5')
        :type custom: dict
        :param drift: drift correction settings (if None, then no drift correction is performed).
            for example: dict(x=0, y=0)
        :type drift: dict
        :return: failure or success
        :rtype: bool
        """
        if ptw is not None:
            self.set_display(ptw)

        if not self.dummy_mode:
            try:
                self.set_calibration()

                if custom is not None:
                    # Set custom calibration
                    ctype = custom['ctype']
                    del custom['ctype']
                    x, y = self.calibration.generate_cal_targets(**custom)
                    self.calibration.custom_calibration(x=x, y=y, ctype=ctype)
                self.calibration.calibrate()

                if drift is not None:
                    # Perform drift correction
                    self.calibration.driftcorrection(**drift)

                # Unset display and calibration instance
                self.unset_display()
                self.unset_calibration()

                return True
            except RuntimeError as e:
                self.logger.error('[{}] Error during calibration: {}'.format(__name__, e))
                raise RuntimeError(e)
        else:
            return False

    def record(self, stimuli):
        """
        Record stimuli position into data file
        :param stimuli: dictionary providing stimuli position: for example, dict('stimulus_name'=>[float, float, float])
        :type stimuli: dict
        :return: success or failure
        :rtype: bool
        """
        datatowrite = 'STIM '
        for stimulus, pos in stimuli.iteritems():
            datatowrite = ' '.join((datatowrite,
                                    '{} {}'.format(stimulus.upper(), self.position_to_str(pos))))
        self.send_message(datatowrite)

    @staticmethod
    def position_to_str(position):
        """
        Convert position to string
        :param position:
        :return: string
        """
        converted = ' '.join(str(n) for n in position)
        return converted


class EDFfile(object):
    """
    Hand EDF file
    open(): open file
    close(): close file and retrieve it from the eyelink computer
    retrieve(): retrieve file from eyelink's computer
    """

    def __init__(self, tracker, name):
        """
        Constructor of EDFfile class
        :param EyeTracker tracker: EyeTracker
        :param string name: full path to destination file
        """
        self.tracker = tracker
        self.edfname = "{}.edf".format(random.randint(1000, 9999))  # EDF file name stored on the EL host (4 char max)
        self.name = "{}.edf".format(name)

    def open(self):
        """
        Open EDF file
        """
        logging.getLogger('EasyExp').info('[{0}] Opening data file "{1}"'.format(__name__, self.edfname))

        try:
            self.tracker.el.openDataFile(self.edfname)
        except Exception as e:
            raise e

    def close(self):
        """
        Close data file
        """
        logging.getLogger('EasyExp').info('[{0}] Closing data file {1}'.format(__name__, self.edfname))
        self.tracker.el.closeDataFile()
        self.retrieve()

    def retrieve(self):
        """
        Retrieve file from eyetracker computer
        :return:
        """
        self.tracker.el.receiveDataFile(self.edfname, self.name)


# Constants
TRIAL_OK = 0
IN_RECORD_MODE = 4

CR_HAIR_COLOR = 1
PUPIL_HAIR_COLOR = 2
PUPIL_BOX_COLOR = 3
SEARCH_LIMIT_BOX_COLOR = 4
MOUSE_CURSOR_COLOR = 5

_dummy_names = [
    'setSaccadeVelocityThreshold', 'setAccelerationThreshold',
    'setUpdateInterval', 'setFixationUpdateAccumulate', 'setFileEventFilter',
    'setLinkEventFilter', 'setFileSampleFilter', 'setLinkSampleFilter',
    'setPupilSizeDiameter', 'setAcceptTargetFixationButton',
    'openDataFile', 'startRecording', 'waitForModeReady',
    'isRecording', 'stopRecording', 'closeDataFile', 'doTrackerSetup',
    'receiveDataFile', 'close', 'sendCommand', 'isConnected',
    'setOfflineMode', 'getTrackerVersion', 'setCalibrationType', 'commandResult'
]


def dummy_fun(*args, **kwargs):
    """A dummy function used by EL dummy mode"""
    return TRIAL_OK


class DummyMode(object):
    """
    Dummy client: simulates eyes by using mouse position
    """

    def __init__(self):
        """
        DummyMode constructor
        """

        for name in _dummy_names:
            setattr(self, name, dummy_fun)
        self.elTrackerVersion = lambda: 'Dummy'
        self.elDummyMode = lambda: True
        self.elCurrentMode = lambda: IN_RECORD_MODE
        self.waitForBlockStart = lambda a, b, c: 1
        self.__fakedEye = None
        logging.getLogger('EasyExp').debug('[{}] !!! You are entering the Dummy Mode: Eye movements will be simulated '
                                           'with the mouse !!!'.format([__name__]))

    def sendMessage(self, msg):
        """
        Overrides sendMessage method and only prints out the message in console
        :param msg: message to send to tracker
        :type msg str
        """
        if not isinstance(msg, str):
            raise TypeError('msg must be str')
        logging.getLogger('EasyExp').debug('[{0}] Message sent to eyelink: {1}'.format(__name__, msg))

    def sendCommand(self, cmd):
        """
        Overrides sendCommand method and only prints out the message in console
        :param cmd: command to send to tracker
        :type cmd str
        """
        if not isinstance(cmd, str):
            raise TypeError('msg must be str')
        logging.getLogger('EasyExp').debug('[{0}] Command sent to eyelink: {1}'.format(__name__, cmd))

    def getTrackerVersion(self):
        """
        Overrides getTrackerVersion method and return an arbitrary version number
        :return int
        """
        return "3"

    def eyeAvailable(self):
        """
        Return eye available to tracker, but here the eye is the mouse
        :return int
        """
        return 3

    def getNewestSample(self):
        return FakeSample()

    def getNextData(self):
        return self.getNewestSample()


class FakeSample(object):

    def __init__(self):
        self.__fakeEye = None

    def isRightSample(self):
        return True

    def isLeftSample(self):
        return True

    def getRightEye(self):
        pass

    def getLeftEye(self):
        pass


EYE_MISSING = -32768


class Eye(object):
    """
    Handle eye status and position
    """

    def __init__(self, tracker, eye_id):
        """
        Eye Constructor
        :param tracker: EyeTracker instance
        :type tracker EyeTracker
        :param eye_id: Eye id
        :type eye_id str
        """
        self.tracker = tracker
        self.id = eye_id
        self.x = 0
        self.y = 0
        self.blink = False
        self.status = False
        self.__position_tracker = PositionTracker()
        self.__fixation_checker = FixationChecker(tracker)

    def __str__(self):
        """
        Print method
        """
        return "Eye '%s' | x:%.1f y: %.1f | Missing: %s" % (self.id, self.x, self.y, self.missing)

    def get_status(self):
        """
        Get eye's status

        """
        self.status = self.missing | self.blink

    @property
    def missing(self):
        return self.x == EYE_MISSING or self.y == EYE_MISSING

    def get_position(self, sample_type='newest'):
        """
        Get eye samples for the recorded eye
        :param sample_type:
        """
        if self.id is not 'MOUSE':
            if sample_type is 'newest':
                dt = self.tracker.el.getNewestSample()  # check for new sample update
            else:
                dt = self.tracker.el.getNextData()  # Get oldest sample
                dt = None if dt == 200 else dt

            if dt is not None:
                # Gets the gaze position of the latest sample,
                if self.id == 'RIGHT_EYE' and dt.isRightSample():
                    self.x, self.y = dt.getRightEye().getGaze()
                elif self.id == 'LEFT_EYE' and dt.isLeftSample():
                    self.x, self.y = dt.getLeftEye().getGaze()
            else:
                self.x, self.y = 0, 0
        else:
            minput = self.tracker.display.gui.get_mouse_state()
            self.x, self.y = minput.__position__
            # self.tracker.display.gui.draw_eye(self.x, self.y, flip=False)

        self.get_status()

        self.__position_tracker.add_history(self.position)

        return self.x, self.y, self.status

    @property
    def position(self):
        """
        Return eye position
        :return: horizontal and vertical position of the gaze
        :rtype: list
        """
        return np.array([self.x, self.y])

    @property
    def velocity(self):
        """
        Return eye velocity
        :return: eye velocity in m/s
        """
        return self.__position_tracker.velocity

    def validate(self, position, radius, duration):
        """
        Validate end position of sensor: sensor must not move for a given duration to be considered as stable
        :param position: reference position
        :type position: ndarray
        :param radius: tolerance radius (in pixels)
        :type radius: float
        :param duration: duration of validation period (in seconds)
        :type duration: float
        :rtype: bool
        """
        return self.__fixation_checker.validate(position, radius, duration)

    def reset_validator(self):
        """
        Reset fixation validator
        :return: void
        """
        self.__fixation_checker.reset()

    def draw(self):
        """
        Draw eye
        :return:
        """
        self.tracker.display.gui.draw_eye(self.x, self.y, flip=False)


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
        if self.__tOld is not None:
            self.__dt = time.time() - self.__tOld

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
            try:
                return float(np.mean(np.array(distances) / np.array(self.__intervals)))
            except ZeroDivisionError:
                return 0.0
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


class Display(object):
    """
    This class handles display used by the tracker for calibration
    """

    def __init__(self, tracker, dummy=False, display_type='psychopy', distance=550, resolution=(1024, 768),
                 winsize=(400, 300), bgcol=(0, 0, 0), inner_tgcol=(1, 1, 1), outer_tgcol=(0, 0, 0), targetsize_in=0.5,
                 targetsize_out=1.5, ptw=None):
        """
        Display constructor
        :param tracker
        :type tracker EyeTracker
        :param dummy: Dummy mode
        :type dummy bool
        :param display_type: window type ('pygame', 'psychopy', 'qt')
        :type display_type str
        :param distance: distance eye-screen in mm
        :type distance int
        :param resolution: screen resolution (in pixels)
        :type resolution tuple
        :param winsize: screen size (in mm)
        :type winsize tuple
        :param bgcol: background color (for calibration)
        :type bgcol tuple
        :param inner_tgcol: inner calibration target color
        :type inner_tgcol tuple
        :param outer_tgcol: outer calibration target color
        :type outer_tgcol tuple
        :param targetsize_in: inner calibration target radius (in visual angles)
        :type targetsize_in float
        :param targetsize_out: outer calibration target radius (in visual angles)
        :type targetsize_out: float
        :param ptw: window's pointer
        """

        self.tracker = tracker  # Link to eye tracker
        self.dummy = dummy  # dummy mode
        self.display_type = display_type  # display type
        self.distance = distance  # distance screen/eyes (in mm)
        self.resolution = resolution  # screen's resolution (in pixels)
        self.winsize = winsize  # screen's size (in mm)
        self.bgcol = bgcol  # background color

        self.ptw = ptw  # Window/QtApp pointer
        self.gui = None  # Eye tracker GUI
        self.center = 0.5*resolution[0], 0.5*resolution[1]  # Screen center
        self.inner_tgcol = inner_tgcol  # Color of inner target
        self.outer_tgcol = outer_tgcol  # Color of outer target
        self.targetsize_out = targetsize_out  # Size of outer target
        self.targetsize_in = targetsize_in  # Size of inner target

        # Initialize GUI
        self.init()

    def init(self):
        """
        Initialization of display
        :return:
        """
        if self.ptw is None:
            RuntimeError('You must provide a window/Qt application pointer')

        print(self)

        # Convert target size from visual angles to pixels
        targetsize_out = deg2pix(self.targetsize_out, 1, self.distance, self.resolution, self.winsize)
        targetsize_in = deg2pix(self.targetsize_in, 1, self.distance, self.resolution, self.winsize)

        if self.display_type == 'pygame':
            from display.display_pygame import DisplayPygame
            self.gui = DisplayPygame(self.tracker)
        elif self.display_type == 'qt':
            from display.qeyelink import QEyelink
            self.gui = QEyelink(self.tracker)
        elif self.display_type == 'psychopy':
            from display.display_psychopy import EyeLinkCoreGraphicsPsychopy
            self.gui = EyeLinkCoreGraphicsPsychopy(self.tracker, self.ptw, dummy=self.dummy, bgcol=self.bgcol,
                                                   outer_target_size=targetsize_out,
                                                   inner_target_size=targetsize_in,
                                                   outer_target_col=self.outer_tgcol,
                                                   inner_target_col=self.inner_tgcol)

    def __str__(self):
        return '\n.:: EYETRACKER GUI::. \n' \
               'Initialisation of {} window:\n' \
               'Resolution (pixels): {}\n' \
               'Display size (mm): {}'.format(self.display_type, self.resolution, self.winsize)


class Calibration(object):
    """
    Calibration class
    Handles Eyetracker calibration routines
    Calibration::setup(): calibration setup. Defines calibration types, target number, position,
    sequence of presentation
    """

    def __init__(self, tracker, screen=Display, cal_type='HV5'):
        """
        Calibration class constructor
        :param tracker: EyeTracker class instance
        :type tracker EyeTracker
        :param screen: Display class instance
        :type screen Display
        :param cal_type: calibration type (e.g.: HV5, H3)
        :type cal_type str
        """
        self.tracker = tracker
        self.display = screen
        self.ctype = cal_type
        self.last = time.time()
        self.lost = 0

        # Setup calibration
        self.setup()
        self.setup_cal_sound()

    def set_display(self, new_display=Display):
        self.display = new_display

    def setup(self):
        """
        Setup calibration
        :return:
        """
        # Calibration settings
        logging.getLogger('EasyExp').debug('[{0}] Calibration type set to {1}'.format(__name__, self.ctype))

        # Set display coordinates
        self.getgraphicenv()

        # self.tracker.send_command("calibration_type = {}".format(self.ctype))
        self.tracker.send_command("binocular_enabled = {}".format(self.tracker.trackedeye is BINOCULAR))
        # self.tracker.send_command("enable_automatic_calibration = YES")

        # switch off the randomization of the targets
        # self.tracker.send_command("randomize_calibration_order = NO")
        # self.tracker.send_command("randomize_validation_order = NO")

        # prevent it from repeating the first calibration point
        # self.tracker.send_command("cal_repeat_first_target = NO")
        # self.tracker.send_command("val_repeat_first_target = NO")

        # so we can tell it which targets to use
        # self.tracker.send_command("generate_default_targets = YES")

        # Sets the calibration target and background color
        setCalibrationColors(self.display.outer_tgcol, self.display.bgcol)

    def custom_calibration(self, x, y, ctype=None):
        """
        Custom calibration setup
        :param x: list of horizontal targets coordinates
        :type x tuple
        :param y: list of vertical targets coordinates
        :type y tuple
        :param ctype: calibration type
        :type ctype str
        """
        ctype = ctype if ctype is not None else self.ctype

        nb_samples = len(x)

        # Generates sequence list
        sequence_index = ','.join(['{}'.format(i) for i in range(0, nb_samples+1)])

        # Generates calibration targets list
        calibration_targets = ' '.join(['{0:d},{1:d}'.format(int(x[i]), int(y[i])) for i in range(len(x))])

        # Generates validation targets list
        validation_targets = ' '.join(['{0:d},{1:d}'.format(int(x[i]), int(y[i])) for i in range(len(x))])

        print(sequence_index)
        print(calibration_targets)
        print(validation_targets)

        logging.getLogger('EasyExp').info('[{}] ### Using custom calibration ###'.format(__name__))
        logging.getLogger('EasyExp').info('[{0}] Sequence index: {1}'.format(__name__, sequence_index))
        logging.getLogger('EasyExp').info('[{0}] Calibration targets: {1}'.format(__name__, calibration_targets))

        # Set graphics
        self.getgraphicenv()

        # Prevent Eye-tracker generating default targets
        self.tracker.send_command("calibration_type = %s" % ctype)
        self.tracker.send_command('generate_default_targets = NO')

        # Set calibration sequence
        self.tracker.send_command('calibration_samples = {}'.format(nb_samples))
        self.tracker.send_command('calibration_sequence = {}'.format(sequence_index))
        self.tracker.send_command('calibration_targets = {}'.format(calibration_targets))

        # Set validation sequence
        self.tracker.send_command('validation_samples = {}'.format(nb_samples))
        self.tracker.send_command('validation_sequence = {}'.format(sequence_index))
        self.tracker.send_command('validation_targets = {}'.format(validation_targets))

    def getgraphicenv(self):
        """
        Get graphical environment (screen resolution, size)
        :return:
        """
        self.tracker.send_command('screen_pixel_coords = {0:d} {1:d} {2:d} {3:d}'
                                  .format(0, 0, int(self.display.resolution[0])-1, int(self.display.resolution[1])-1))
        self.tracker.el.sendMessage('DISPLAY_COORDS {0:d} {1:d} {2:d} {3:d}'
                                    .format(0, 0, int(self.display.resolution[0])-1, int(self.display.resolution[1])-1))

    def setup_cal_sound(self):
        """
        Set calibration sounds
        """
        setCalibrationSounds("", "", "")
        setDriftCorrectSounds("", "off", "off")

    def calibrate(self):
        """
        Perform a calibration
        """
        logging.getLogger('EasyExp').info('[{}] Start Calibration'.format(__name__))

        # Switch calibration display on
        openGraphicsEx(self.display.gui)

        self.lost = 0
        self.last = time.time()

        # Perform calibration
        self.tracker.el.doTrackerSetup()

        # Close calibration display
        logging.getLogger('EasyExp').info('[{}] Exit Calibration'.format(__name__))

    def driftcorrection(self, x, y, draw=1):
        """
        Perform a drift correction
        :param y: vertical position of target
        :param x: horizontal position of target
        :param draw:
        """
        # The following does drift correction at the begin of each trial
        while 1:
            # Checks whether we are still connected to the tracker
            if not self.tracker.el.isConnected():
                self.tracker.close()

            # Does drift correction and handles the re-do camera setup situations
            try:
                error = self.tracker.el.doDriftCorrect(x, y, draw, 0)
            except Exception as e:
                raise Exception("[{}] Drift correction failed: {}".format(__name__, e))
            else:
                logging.getLogger('EasyExp').info("[{0}] Drift result: {1}".format(__name__, error))
                if error != 27:
                    break
                else:
                    self.calibrate()
        logging.getLogger('EasyExp').info("[{}] Drift correction successfully performed".format(__name__))

    def generate_cal_targets(self, radius, n, shape='rect'):
        """
        Generate calibration targets coordinates
        :param shape: Calibration type
        :type shape: str
        :param radius: distance of targets from screen center
        :type radius: float
        :param n: number of points
        :type n: int
        :return: ndarray, ndarray
        """
        if n not in [5, 9]:
            raise AttributeError('EyeLink only accepts 5- or 9-points calibration grids')

        if shape == 'rect':
            if n == 5:
                x = radius * np.array([-1, 1, 0, -1, 1]) * (self.display.resolution[0] / 2)
                y = radius * np.array([1, 1, 0, -1, -1]) * (self.display.resolution[1] / 2)
                x += 0.5 * self.display.resolution[0]  # Center coordinates on screen center
                y += 0.5 * self.display.resolution[1]
            else:
                x = radius * np.array([-1, 0, 1, -1, 0, 1, -1, 0, 1]) * (self.display.resolution[0] / 2)
                y = radius * np.array([1, 1, 1, 0, 0, 0, -1, -1, -1]) * (self.display.resolution[1] / 2)
                x += 0.5 * self.display.resolution[0]  # Center coordinates on screen center
                y += 0.5 * self.display.resolution[1]
        elif shape == 'sphere':
            x, y = self.pol2cart(0.5 * (self.display.resolution[0] / 2), np.linspace(0, 7 * np.pi / 4, n-1))
            x += 0.5 * self.display.resolution[0]  # Center coordinates on screen center
            y += 0.5 * self.display.resolution[1]
            x = np.insert(x, 0, 0.5 * self.display.resolution[0])
            y = np.insert(y, 0, 0.5 * self.display.resolution[1])
        else:
            raise AttributeError('Unknown calibration shape: "{}". Possible options are "rect" or "sphere"'.format(
                shape))

        return x, y

    @staticmethod
    def pol2cart(rho, phi):
        """
        Converts polar to cartesian
        Parameters
        ----------
        rho
        phi

        Returns
        -------
        :rtype: ndarray
        """
        x_output = rho * np.cos(phi)
        y_output = rho * np.sin(phi)
        return x_output, y_output


class Checking(object):
    """
    Handle checking routines:
    fixationtest(): perform a fixation test by controlling fixation on a target for a certain period of time. The test
    only stops once the fixation is correct.
    fixationcheck(): check if the eyes stay within a particular region of space
    calibratoncheck(): check if a calibration is requested
    """

    def __init__(self, tracker, display, radius=1.5):
        """
        Constructor
        :param tracker: instance of EyeTracker class
        :type tracker EyeTracker
        :param display: instance of Display class
        :type display Display
        :param radius
        :type radius float
        """
        self.tracker = tracker
        self.display = display
        self.radius = radius

        self.lost = 0  # Number of time the eye has been lost so far
        self.lostthres = 20  # Maximum Number of looses before we redo a calibration
        self.timebtwcal = 10  # Time interval between two calibration
        self.timecal = None  # Time of last calibration
        self.time_lastcal = None
        self.auto = False
        self.time_to_fixate = 1
        self.fixation_duration = 0.200

        # Convert radius from visual angles to pixels
        self.radius = deg2pix(self.radius, 1, self.display.distance, self.display.resolution, self.display.winsize)[0]

    def fixationtest(self, opt='fix', fixation_duration=0.2, time_to_fixate=1, radius=None, rx=0, ry=0):
        """
        Draw a fixation dot till the subject has fixated at it during a specific
        time. The dot is either drawn on the screen center (opt: "fix"), or at a
        position randomly chosen across the screen at the beginning of every
        presentation (opt: "rnd"). "w" is the tolerance radius around
        the fixation point (in pixels).
        :param time_to_fixate:
        :type time_to_fixate: int
        :param str opt:
        :type fixation_duration: float
        :param radius: tolerance radius
        :type radius: float
        :param rx: horizontal coordinate of fixation point
        :param ry: vertical coordinate of fixation point
        :return bool fix:
        """
        logging.getLogger('EasyExp').info('[{}] Start fixation test'.format(__name__))
        self.tracker.el.sendMessage('EVENT_FIXATION_TEST_START')

        if radius is not None:
            self.radius = deg2pix(radius, 1, self.display.distance, self.display.resolution,
                                  self.display.winsize)[0]  # Radius (in deg) of the fixation area
        if self.display.display_type == 'psychopy' and self.display.ptw.units == 'norm':
            self.radius = float(self.radius)/float(self.display.resolution[0])

        fix = False
        msg_duration = 0.5
        quit = False

        # Clear the screen
        self.display.gui.clear_cal_display()

        # start fixation loop
        if not fix and not quit:
            if opt == 'manual':
                pass
            elif opt == 'fix':
                rx = self.display.center[0]
                ry = self.display.center[1]
            elif opt == 'rnd':
                rx = random.choice(range(0, self.display.resolution[0], 10))
                ry = random.choice(range(0, self.display.resolution[1], 10))
            else:
                raise AttributeError('[{0}] "{1}" is not a valid option. '
                                     'Please, choose either "fix" or "rnd"'.format(__name__, opt))

            # Draw Fixation Point
            self.display.gui.draw_cal_target(rx, ry)

            testtime_end = time_to_fixate + time.time()
            fixating = False
            if time.time() < testtime_end and not fixating and not quit:
                quit = self.checkforcalibration()

                # Test whether the target eye is within the fixation window (radius from fixation point)
                fixating = self.fixationcheck(rx, ry)

            # If yes, we add an extra time of fixation, just to make sure the eye
            # did not fall within the fixation window by accident
            if fixating:
                fixtime_end = time.time() + fixation_duration
                fixating = False
                if time.time() < fixtime_end and not quit:
                    quit = self.checkforcalibration()

                    # Test whether the target eye is within the fixation window (radius from fixation point)
                    fixating = self.fixationcheck(rx, ry)

            if fixating:
                fix = True

            # If participant did not fixate the target, we ask him/her to do so
            if not fix:
                self.display.gui.draw_cal_target(rx, ry)
                self.display.gui.showmsg(msg='Fixate', color=(1, 1, 1))
                msgtime_end = time.time() + msg_duration
                if time.time() < msgtime_end and not quit:
                    quit = self.checkforcalibration()

            # Blank the screen out
            self.display.gui.clear_cal_display()

        self.tracker.el.sendMessage('EVENT_FIXATION_TEST_END')
        return fix

    def fixationcheck(self, cx=0, cy=0):
        """
        Check is eye's location relative to a reference point.
        :param cx horizontal position of area center
        :param cy vertical position of area center
        :return bool fix
        """
        fix = []
        mx, my, status = self.tracker.eye.get_position('newest')
        fix.append(self.inrange(mx, my, cx, cy))

        # Check if we need to redo a calibration
        if True not in fix:
            self.time_lastcal = self.tracker.calibration.last
            if self.time_lastcal > self.timebtwcal:
                self.lost = 0
            else:
                self.lost += 1
            if self.auto & self.lost > self.lostthres:
                self.tracker.calibration.calibrate()
                self.tracker.start_recording(self.tracker.trial)
                return

        return True in fix

    def inrange(self, mx, my, cx, cy):
        """
        Check if eye position falls within a given range from a target location defined by cx, cy
        :param: mx, my: coordinates of the eye or mouse
        :param: cx, cy: coordinates of the reference point
        """
        r = math.sqrt((mx - cx) ** 2 + (my - cy) ** 2)
        return r <= self.radius

    def checkforcalibration(self):
        """
        Do a calibration if asked
        :return void
        """
        keys = self.display.gui.get_input_key()
        for key in keys:
            if key:
                logging.getLogger('EasyExp').debug('[{0}] Key "{1}" has been pressed'.format(__name__, key))
                if key.__key__ == ord('c'):
                    logging.getLogger('EasyExp').debug('[{0}] Calibration requested by the user'.format(__name__))
                    self.tracker.calibration.calibrate()
                    self.tracker.start_recording()
                    return True
                elif key.__key__ == ESC_KEY:
                    logging.getLogger('EasyExp').debug('[{}} Esc pressed, exiting fixation test'.format(__name__))
                    self.tracker.el.sendMessage('EVENT_FIXATION_TEST_ABORTED')
                    return True
                return False
            else:
                return False


class FixationChecker(object):
    """
    FixationChecker
    Handles validation procedure for eye fixation
    Eye is fixating if its position stays within a defined spatial region for a minimum amount of time
    """

    def __init__(self, tracker):
        """
        FixationChecker constructor
        :param tracker: EyeTracker instance
        :type tracker: EyeTracker
        """
        self.__tracker = tracker
        self.__responseChecking = False
        self.__done = False
        self.__responseChecking_start = time.time()

    def validate(self, position, radius, duration):
        """
        Check if the gaze stays within the same spatial region
        :param position: Reference position
        :type position: ndarray
        :param radius: tolerance radius
        :type radius: float
        :param duration: length of validation period (in seconds)
        :type duration: float
        :rtype: bool
        """
        if not self.__done:
            status = self.__checkposition(position, radius)

            if status:
                if not self.__responseChecking:
                    self.__tracker.logger.info('[{}] Start checking'.format(__name__))
                    self.__responseChecking_start = time.time()
                    self.__responseChecking = True
                else:
                    self.__done = (time.time() - self.__responseChecking_start) >= duration
                    if self.__done:
                        self.__tracker.logger.info('[{}]Position validated'.format(__name__))
            else:
                self.__responseChecking = False
        return self.__done

    @property
    def done(self):
        return self.__done

    def reset(self):
        """
        Reset checker
        :return:
        """
        self.__done = False
        self.__responseChecking = False
        self.__responseChecking_start = time.time()

    def __checkposition(self, (x, y), radius):
        """
        Check that the tracked hands are located within a range from a given position
        :param radius:
        :return:
        """
        ref_position = np.array((x, y))
        distance = FixationChecker.distance(ref_position, self.__tracker.eye.position)
        return distance <= radius

    @staticmethod
    def distance(start, end):
        """
        Compute spherical distance between two given points
        :param start: starting position
        :type start: ndarray
        :param end: end position
        :type end: ndarray
        :return:
        """
        x_diff = end[0] - start[0]
        y_diff = end[1] - start[1]
        distance = math.sqrt(x_diff**2+y_diff**2)
        return distance


