#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Snaky_experiment

# Copyright © 2013, W. van Ham, Radboud University Nijmegen
# This file is part of Sleelab.
#
# Sleelab is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sleelab is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sleelab.  If not, see <http:#www.gnu.org/licenses/>.

from __future__ import print_function
import math
import time
import numpy as np
from os.path import isfile

# PyQt
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtOpenGL import *

# openGL
import OpenGL
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.arrays import vbo
from OpenGL.GL.shaders import *

# ExpFrame modules
from core.User import User
from core.Trial import Trial
from core.Screen import Screen
from core.misc.conversion import pol2cart, deg2m, mm2pix
from core.movie.moviemaker import MovieMaker
from core.buttons.buttons import Buttons
from core.apparatus.sled.mysled import MySled
from core.system.customlogger import CustomLogger
from core.display.fpscounter import FpsCounter
from core.opengl import transforms, objects, shader
from core.events.feedback import FeedBack


# Import sound
from psychopy import sound

OpenGL.ERROR_ON_COPY = True  # make sure we do not accidentally send other structures than numpy arrays


class RunTrial(QGLWidget):
    """
    Experiment QGL widget
    # Coordinate system:
    # The center of the screen is the origin of the model coordinate system.
    # Dimensions are in coherent international units (m, s, m/s, ...).
    # The viewer sits at pViewer. pViewer[2] (the distance to the screen)
    # must not change during the experiment. It is always positive.
    # The x-direction is to the right of the viewer, the y-direction is up.
    # Hence the coordinate system  is right handed.
    # dScreen is the dimension of the screen in m. If the height-width
    # ratio of the screen is different from the height-width ratio (in
    # pixels) of the window, then this program will assume that the pixels
    # are not square.
    # Objects are only drawn if they are between zNear and zFar.
    # Stars are always between zNearStar and zFarStar,
    # these are the experiment parameters.json zNear and zFar.
    """

    def __init__(self, trial=Trial, screen=Screen, user=User):
        """
        Class constructor
        :param Trial trial: instantiation of Trial class
        :param Screen screen: instantiation of Screen class
        :param User user: instantiation of User class
        :return:
        """
        super(RunTrial, self).__init__(screen.ptw)

        self.screen = screen
        self.user = user
        self.trial = trial
        self.actions = {}

        self.setup()
        self.setcontrols()

        # Experiment's settings
        # =====================
        # space
        self.pViewer = np.array([0, 0, self.screen.distance/1000.0])  # m, x,y,z-position of the viewer
        self.zNear = 0.5 * self.pViewer[2]  # m  viewable point nearest to viewer, now exp. var
        self.zFocal = 0  # m, position of physical screen, do not change this
        self.zFar = -0.5 * self.pViewer[2]  # m, viewable point furthest from viewer, now exp. var
        self.dScreen = np.array((self.screen.width_mm/1000.0, self.screen.height_mm/1000.0))  # m, size of the screen
        self.width = self.screen.width_px
        self.height = self.screen.height_px

        # Get User info
        self.dEyes = user.dEye  # inter-eyes spacing

        # balls
        self.nLands = int(self.trial.parameters['nLands'])  # Number of landmarks
        self.nBalls = self.nLands + 1  # Total number of balls: 1 target + n landmarks
        self.rBalls = float(self.trial.parameters['rBalls'])  # ball radius in m

        # Depth limit
        self.nearPlan = float(self.zNear-1.2*self.rBalls)
        self.maxDepth = float(self.trial.parameters['depth_final'])
        self.initDepth = float(self.trial.parameters['depth_init'])

        # Landing limit
        self.landingLimit = float(self.trial.parameters['y_final'])

        # Stimuli trajectories
        # ====================
        self.trajectories_file = '{}/{}_trajectories.json'.format(screen.expfolder, user.base_file_name)
        self.sub_trajectories_file = '{}_trajectories.json'.format(user.dftName)
        if not isfile(self.trajectories_file):
            # Generates object trajectories if it has not been done yet
            OrnsteinInertia.run(design_file=self.trial.design.userfile, trajectories_file=self.trajectories_file,
                                start_y=self.trial.parameters['y_init'], start_z=self.initDepth, end_y=self.landingLimit,
                                end_z=self.maxDepth, sig_v=self.trial.parameters['sigV'],
                                inertia=self.trial.parameters['inertia'], fixed_dt=1.0,
                                duration=self.trial.parameters['ballsMvtDuration'],
                                target_time=self.trial.parameters['target_time'],
                                fixed=(False, False, True))

        if not isfile(self.sub_trajectories_file):
            # Copy trajectories file into participant's folder
            from shutil import copy
            copy(self.trajectories_file, self.sub_trajectories_file)

        # Load trajectories
        self.trajectories = OrnsteinInertia.load_trajectories(self.trajectories_file)

        # Feedback generator
        self.feedback = FeedBack(frequency=int(self.trial.settings['feedbackInt']))

        # Sled settings
        # =============
        self.sledHome = 0.0  # Sled homing position (in m)
        self.movDurationBack = 2.0  # Movement duration in seconds when returning home
        self.sledStart = float(self.trial.parameters['sledStart'])  # Sled starting position (in m)
        self.movDuration = float(self.trial.parameters['movDuration'])  # Movement duration in seconds
        self.movDistance = float(self.trial.parameters['movDistance'])  # Movement amplitude in meters
        self.sledFinal = self.sledStart + self.movDistance  # Sled final position (in m)
        self.side = 1

        # Events duration
        # =============
        self.durations = self.trial.parameters['durations']
        self.ballsMvtDuration = self.trial.parameters['ballsMvtDuration']  # Stimulus duration in s

        # Devices
        # =======
        # Import sled client or its simulator
        self.sled = MySled(status=self.trial.settings['sled'], server='sled')

        # Import Optotrack client
        # Distance in m of "origin" sensor to the sled's center
        self.xOrigintoCenter = float(self.trial.parameters['OriginToCenter'])
        self.optoTimeThres = 0.050  # Temporal threshold during which the hand has to remain within the same location
        self.velocityThres = 0.01  # Velocity threshold below which the hand is considered as stationary
        self.homeFromHand1 = np.array((self.xOrigintoCenter, 0, 0))
        optofilename = '{}'.format(user.dftName)  # Optotrak data filename
        self.optotrack = OptoTrack(optofilename, freq=200.0, velocityThres=self.velocityThres,
                                   timeWindow=self.optoTimeThres, origin='origin',
                                   labels=('Xas', 'Marker2', 'Yas', 'origin', 'hand1', 'hand2'),
                                   status=self.trial.settings['optotrack'],
                                   trackedhand={'Xas', 'Marker2', 'Yas', 'origin', 'hand1', 'hand2'})
        self.optotrack.init()
        self.initHandPosition = (0.0, 0.0, 0.0)  # screen center

        if not self.trial.settings['optotrack']:
            # If running in dummy mode (debugging)
            self.sledCenter = (0.0, 0.0, 0.0)  # screen center
            self.radiusOn = 50  # pixels
            self.radiusOff = 50  # pixels
        else:
            # If running in experiment
            # Distance of rail extremity (marker hand1) to sled center
            self.sledCenter = self.optotrack.sensors['hand1'].getPosition() + self.homeFromHand1
            self.radiusOn = 0.03  # m
            self.radiusOff = 0.03  # m
        self.homePosition = 0.0

        # Video/Audio
        # ======
        # GL settings
        self.setgl(1)
        self.fadeFactor = 1.0  # no fade, fully exposed

        # Initialize audio
        self.sounds = {}
        self.init_audio()

        # Prepare stimuli
        self.stimuli = {}
        self.landspacing = 0.40
        self.predict = None
        self.objects = {}
        self.pong_position = np.array((0.0, 0.0, 0.0))

        # OpenGL
        # ======
        self.program = None

        # dynamic uniforms
        self.MVPLocation = None
        self.nFrameLocation = None
        self.fadeFactorLocation = None
        self.colorLocation = None
        self.offsetLocation = None

        # attributes
        self.positionLocation = None

        # Event triggers
        # ==============
        self.running = False  # running mode
        self.triggers = {
            'startTrigger': False,
            'checkTrigger': False,
            'updateTrigger': False,
            'pauseRequested': False,
            'stimulusTrigger': False,
            'targetVisible': False,
            'responseTrigger': False,
            'motionTrigger': False,
            'feedback': False
        }

        self.PositionChecker = None
        self.tracking = None

        self.textToDraw = None
        self.validMvt = False
        self.validTrial = False

        # Timer
        self.timers = {
            'stimulusDuration': None,
            'responseDuration': None,
            'mvtDuration': None,
            'sledDuration': None
        }

        self.data = {
            'requested_target_position': None,
            'final_target_position': None,
            'final_hand_position': None,
            'final_landL_position': None,
            'final_landR_position': None,
            'sled_at_response': None,
            'final_sled_position': None,
            'trialDuration': None,
            'responseDuration': None,
            'sledDuration': None,
            'mvtLatency': None,
            'mvtDuration': None,
            'correct': None,
        }

        # Trigger fullScreen and stereoscopic modes
        self.togglestereo(False)
        self.parent().toggleFullScreen()

        self.state = "home"
        self.changestate()

    def init_audio(self):
        """
        Initialize sounds
        :return:
        """
        # Sound
        self.sounds['valid'] = sound.SoundPygame(secs=0.05, value=880)
        self.sounds['valid'].setVolume(1)

        self.sounds['wrong'] = sound.SoundPygame(secs=0.05, value=440)
        self.sounds['wrong'].setVolume(1)

    def setgl(self, vsync=0):
        """
        Set buffering
        :param vsync:
        :return:
        """
        fmt = self.format()
        # always double buffers anyway (watch NVIDIA setting, do not do it there also in 120 Hz mode)
        fmt.setDoubleBuffer(True)
        fmt.setSampleBuffers(True)
        fmt.setSwapInterval(vsync)  # 0: no sync to v-refresh, number of syncs to wait for
        self.setFormat(fmt)  # PyQt
        if self.format().swapInterval() == -1:
            print("Setting swap interval not possible, expect syncing problems")
        if not self.format().doubleBuffer():
            print("Could not get double buffer; results will be suboptimal")

    def initstimuli(self):
        """
        Initialize stimuli
        :return:
        """
        # Predictability of landmarks' path
        self.predict = self.trial.params['predict']
        if self.predict == '1':
            self.predict = False
        else:
            self.predict = float(self.predict)

        # Target's side (-1: left, 1:right)
        side = 1 if self.trial.params['side'] == 'right' else -1

        # Define starting position of hand
        self.homePosition = self.trial.parameters['homePosition'][0] if side == 1 else self.trial.parameters['homePosition'][1]
        self.initHandPosition = self.sledCenter + np.array((self.homePosition, 0.0, 0.0))

        # Define angle range
        target_final_x = float(self.trial.params['angle'])
        target_start_x = float(self.trial.params['initPos'])

        # Target initial and final location
        end_x_position = self.sledFinal + (target_final_x - self.homePosition)
        start_x_position = self.sledFinal + (target_start_x - self.homePosition)

        target_init_position = np.array((start_x_position, float(self.trial.parameters['y_init']), self.initDepth),
                                        dtype='float32')
        self.data['requested_target_position'] = np.array((end_x_position, float(self.trial.parameters['y_final']),
                                                           self.maxDepth), dtype='float32')
        init_land_x = np.array(self.trial.parameters['init_land_x'])
        self.landspacing = init_land_x[1] - init_land_x[0]

        # Prepare stimuli
        # Target
        self.stimuli[0] = Stimuli(color=np.array([1, 0, 0], 'f'), size=self.rBalls, shape='sphere',
                                  position=target_init_position)
        self.stimuli[0].path = OrnsteinInertia()
        self.stimuli[0].path.set_trajectories(self.trajectories)
        self.stimuli[0].path.load_trajectory(str(self.trial.id), 'target')
        self.stimuli[0].path.trajectory[:, 0] = self.sledFinal + (self.stimuli[0].path.trajectory[:, 0] - self.homePosition)

        # Landmarks
        for s in range(0, self.nLands):
            self.stimuli[s+1] = Stimuli(color=np.array([1, 1, 1], 'f'), size=self.rBalls, shape='sphere',
                                        position=np.array((start_x_position + init_land_x[s],
                                                           float(self.trial.parameters['y_init']),
                                                           self.initDepth)))
            self.stimuli[s+1].path = OrnsteinInertia()
            self.stimuli[s+1].path.set_trajectories(self.trajectories)
            self.stimuli[s+1].path.load_trajectory(str(self.trial.id), 'landmark')
            self.stimuli[s+1].path.trajectory[:, 0] = self.sledFinal + ((self.stimuli[s+1].path.trajectory[:, 0] + init_land_x[s]) - self.homePosition)

    views = ('ALL',)

    def setup(self):
        """
        Setup current instance of Field class
        :return:
        """
        self.setMinimumSize(1400, 525)
        print('Window size: {} {}'.format(self.width(), self.height()))

    def setcontrols(self):
        """
        Set menus and hot keys specific to this widget
        :return:
        """
        # Pause Experiment
        start_icon = QIcon('icon/start.png')
        self.actions['pauseAction'] = QAction(start_icon, '&Pause', self)
        self.actions['pauseAction'].setShortcut('Esc')
        self.actions['pauseAction'].setStatusTip('Pause/Unpause the experiment')
        self.actions['pauseAction'].triggered.connect(self.dopause)

        # Continue Action
        self.actions['continueAction'] = QAction(start_icon, '&Continue', self)
        self.actions['continueAction'].setShortcut(Qt.Key_Space)
        self.actions['continueAction'].setStatusTip('Continue')
        self.actions['continueAction'].triggered.connect(self.gonext)

        # Stereoscopic view
        stereo_icon = QIcon('icon/stereo.png')
        self.actions['stereoAction'] = QAction(stereo_icon, '&Stereoscopic', self)
        self.actions['stereoAction'].setShortcut('Ctrl+S')
        self.actions['stereoAction'].setStatusTip('Toggle Stereoscopic')
        self.actions['stereoAction'].triggered.connect(self.togglestereo)

        # Increase left eye intensity
        self.actions['leftAction'] = QAction('Left intensity', self)
        self.actions['leftAction'].setShortcut("<")
        self.actions['leftAction'].setStatusTip('Increase left eye intensity')
        self.actions['leftAction'].triggered.connect(lambda: self.stereointensity(relative=-1))
        self.actions['leftAction'].setEnabled(False)

        # Increase right eye intensity
        self.actions['rightAction'] = QAction('Right intensity', self)
        self.actions['rightAction'].setShortcut(">")
        self.actions['rightAction'].setStatusTip('Increase right eye intensity')
        self.actions['rightAction'].triggered.connect(lambda: self.stereointensity(relative=1))
        self.actions['rightAction'].setEnabled(False)

        self.addAction(self.actions['stereoAction'])
        self.addAction(self.actions['continueAction'])
        self.addAction(self.actions['pauseAction'])
        self.addAction(self.actions['leftAction'])
        self.addAction(self.actions['rightAction'])

    def gonext(self):
        """
        Start the trial by pressing space
        :return:
        """
        if self.state == 'home':
            self.state = 'iti'
            self.changestate()
        elif self.state == 'pause':
            self.state = 'iti'
            self.changestate()

    def dopause(self):
        """
        Go to pause mode
        :return:
        """
        print('PAUSE REQUESTED')
        self.triggers['pauseRequested'] = True

    def quit(self):
        """
        Exit routine for this widget
        :return:
        """
        print("Quit the experiment")
        # Set in idle mode
        self.state = 'idle'
        self.changestate()

        self.textToDraw = "Experiment is over!"

        # Shutdown the SLED
        self.sled.quit()

        self.optotrack.quit()

    # =========================================
    # State Machine (Trial procedure)
    # =========================================

    initStateTime = None

    def changestate(self):
        """
        states: (sleep), fadeIn, referenceMove, trialMove, wait, fadeOut, home
        state changes are triggered by keys or timers. States always have the same order.
        The sleep state is optional and only occurs if self.requestSleep is true when moving
        out of the home state.
        """
        self.optotrack.sendMessage('STATE_CHANGE_{}'.format(self.state))
        self.textToDraw = None
        if self.initStateTime is None:
            self.initStateTime = time.time()

        stateDuration = time.time() - self.initStateTime
        self.initStateTime = time.time()
        print('[STATE] {0:1.2f}'.format(stateDuration))
        print('[STATE] {}'.format(self.state))

        if self.state == 'idle':
            self.running = False
            return

        elif self.state == 'quit':
            self.running = False
            self.parent().stop_exp()

        elif self.state == "pause":
            # Pause Mode
            self.running = False
            self.triggers['pauseRequested'] = False

            # Move the sled back to its default position
            self.sled.move(self.sledHome, self.movDurationBack)

            self.sled.lights(True)  # Turn the lights ON
            self.textToDraw = 'PAUSE {0}/{1} [Replayed: {2}]'.format(self.trial.nplayed, self.trial.ntrials,
                                                                     self.trial.nreplay)

        elif self.state == "home":
            # Home state: wait for the user to press space to continue
            self.textToDraw = 'Press SPACE to continue'

        elif self.state == "iti":
            # Inter-trial interval: do nothing for a short delay

            # Get trial parameters
            status = self.gettrial()
            if status is False:
                self.state = 'quit'
                self.changestate()
            elif status is 'pause':
                self.state = 'pause'
                self.changestate()
            else:
                # Define state durations
                self.durations['targetOff'] = float(self.trial.params['delay'])
                self.durations['sled_on'] = float(self.trial.parameters['durations']['sled_on']) - float(self.trial.params['delay'])

                # Define inter-trial interval duration
                mov_duration = 0.0 if self.trial.params['mvt'] == 'False' else 1000*self.movDurationBack
                iti_duration = 1000.0*np.random.uniform(
                               float(self.durations['minITIduration']), float(self.durations['maxITIduration']))

                # Move sled to starting position if it is not there already
                self.getviewerposition()
                if np.abs(self.pViewer[0] - self.sledStart) > 0.01:
                    self.sled.move(self.sledStart, self.movDurationBack)
                    self.durations['iti'] = mov_duration + iti_duration
                else:
                    self.durations['iti'] = iti_duration

                # Move the sled back to its home position
                # self.sled.move(self.sledStart, self.movDurationBack)

                self.running = False
                self.state = "start"
                QTimer.singleShot(self.durations['iti'], self.changestate)

        elif self.state == "start":
            # Start the trial if the hands are staying at the initial position
            if self.trial.status:  # If the experiment is not over
                self.running = True
                self.triggers['startTrigger'] = True  # Signal to start checking the hand position

                self.initializeobjects()  # Prepare graphics

                self.sled.lights(False)  # Turn the lights off

            self.tracking = QTimer()
            self.connect(self.tracking, SIGNAL("timeout()"), self.optorecord)
            self.tracking.start(0)

        elif self.state == "stimulus_on":
            # Display stimuli (Sled is not moving)

            self.triggers['startTrigger'] = False
            self.triggers['checkTrigger'] = True
            self.triggers['stimulusTrigger'] = True
            self.triggers['targetVisible'] = True
            self.triggers['updateTrigger'] = True

            self.timers['stimulusDuration'] = time.time()

            self.state = "sled_on"
            QTimer.singleShot(self.durations['stimulus_on'], self.changestate)  # length of viewing targets

        elif self.state == "sled_on":
            # Start sled movement
            self.triggers['motionTrigger'] = True
            self.timers['sledDuration'] = time.time()

            if self.trial.params['mvt'] == "True":
                self.sled.move(self.sledFinal, self.movDuration)

            self.state = "targetOff"
            # QTimer.singleShot(self.durations['to_signal'], self.setsignal)

            QTimer.singleShot(self.durations['sled_on'], self.changestate)

        elif self.state == 'targetOff':
            # Hide target before response
            self.triggers['targetVisible'] = False
            self.data['final_target_position'] = self.stimuli[0].position
            self.state = "stimulus_off"
            QTimer.singleShot(self.durations['targetOff'], self.changestate)

        elif self.state == "response":
            self.sounds['valid'].play()
            self.triggers['checkTrigger'] = False
            self.triggers['responseTrigger'] = True
            self.data['sled_at_response'] = self.pViewer[0]

        elif self.state == "stimulus_off":
            # Remove stimuli
            self.triggers['stimulusTrigger'] = False
            self.data['final_landL_position'] = self.stimuli[1].position
            self.data['final_landR_position'] = self.stimuli[2].position
            self.data['stimulusDuration'] = round((time.time()-self.timers['stimulusDuration'])*1000)
            self.state = 'response'
            self.changestate()

        elif self.state == "response_off":
            # End of response
            self.state = "feedback"

            self.triggers['responseTrigger'] = False
            self.triggers['motionTrigger'] = False
            self.triggers['updateTrigger'] = False
            self.triggers['stimulusTrigger'] = False
            self.running = False

            self.endtrial()  # Save data
            QTimer.singleShot(self.durations['end'], self.changestate)

        elif self.state == "feedback":
            # Show feedback (Practice mode only)
            self.running = True
            self.state = "end"
            if self.trial.settings['practice'] is True or self.feedback.timeToUpdate():
                self.triggers['feedback'] = True
                self.textToDraw = self.feedback.getFeedBack(self.trial.loadData(), self.trial.nplayed)
            else:
                self.triggers['feedback'] = False

            feedback_duration = self.durations['feedback'] if self.triggers['feedback'] else 0.0
            QTimer.singleShot(feedback_duration, self.changestate)

        elif self.state == 'end':
            # End trial routine
            self.triggers['feedback'] = False
            self.running = False

            self.timers['sledDuration'] = round((time.time() - self.timers['sledDuration'])*1000)

            if self.triggers['pauseRequested']:
                self.state = "pause"
            else:
                self.state = 'iti'
            if self.trial.params['mvt'] == "True":
                durationBeforeStart = ((1000*self.movDuration)-self.timers['sledDuration'])
                durationBeforeStart = 0 if durationBeforeStart < 0 else durationBeforeStart
                print('Duration before start {}'.format(durationBeforeStart))
                QTimer.singleShot(durationBeforeStart, self.changestate)  # length of run
            else:
                self.changestate()

    def setsignal(self):
        """
        Set Qtimers
        :return:
        """
        if self.signal is None:
            self.signal = QTimer()
            self.connect(self.signal, SIGNAL("timeout()"), self.playsignal)
            self.signal.start(self.durations['signal'])
            self.signal_nb = 0

    def playsignal(self):
        """
        Play sound to inform the participant to prepare interception
        :return:
        """
        self.signal_nb += 1

        if self.signal_nb <= 2:
            print('Play signal: {}'.format(self.signal_nb))
            self.sounds['valid'].play()
        else:
            self.signal.stop()

    def gettrial(self):
        """
        Get trial's parameters.json
        :return:
        """
        status = self.trial.setup()
        if status is False:
            # If experiment is over
            self.running = False
            return False
        else:
            # Reset timers
            for timer, value in self.timers.iteritems():
                self.timers[timer] = None

            # Reset data
            for data, value in self.timers.iteritems():
                self.data[data] = None

            if status is 'pause':
                # If a pause is requested
                self.triggers['pauseRequested'] = True
            else:
                # Start a new trial
                # Self motion settings
                side = 1 if (self.trial.params['side'] == 'right' or self.trial.params['mvt'] == 'False') else -1
                self.sledStart = side*self.trial.parameters['sledStart']
                self.movDistance = self.trial.parameters['movDistance']
                self.sledFinal = self.sledStart + side*self.movDistance
                if self.trial.params['mvt'] == "False":
                    self.sledStart = self.sledFinal  # Sled homing position (in m)

                print('sled start: {}'.format(self.sledStart))
                print('sled stop: {}'.format(self.sledFinal))
                self.signal = None
                self.PositionChecker = None
                self.optotrack.start_trial(self.trial.id, self.trial.params)
            return status

    def endtrial(self):
        """
        End trial routine
        :return:
        """
        # Is it a valid trial (the subject did not move too soon or too late)?
        self.validTrial = self.data['final_hand_position'] is not False and self.validTrial
        self.tracking.stop()  # Stop recording of hand

        # Did the participant catch the target?
        self.data['correct'] = self.validTrial and np.abs(self.data['final_hand_position'][0] -
                                                          self.data['requested_target_position'][0]) < .05
        self.data['final_target_position'] = self.stimuli[0].path.end_position
        self.data['final_landL_position'] = self.stimuli[1].path.end_position
        self.data['final_landR_position'] = self.stimuli[2].path.end_position
        self.data['trialDuration'] = round(self.trial.endtime*1000)
        self.data['responseDuration'] = self.timers['responseDuration']
        self.data['sledDuration'] = self.timers['sledDuration']
        self.data['final_sled_position'] = self.pViewer[0]
        self.data['mvtDuration'] = self.timers['mvtDuration']

        # Replay the trial if the user did not respond fast enough or moved the hand before the response phase
        print('### Trial {} Results:'.format(self.trial.id))
        for data, value in self.data.iteritems():
            print('{}: {}'.format(data, value))
        print('valid trial:{}'.format(self.validTrial))

        # Feedback
        if not self.validTrial:
            if self.data['mvtLatency'] is None:
                self.textToDraw = 'You must respond'
            elif self.data['mvtLatency']/1000.0 < self.durations['minMvtOnset']:
                self.textToDraw = 'Too early'
            elif self.data['mvtLatency']/1000.0 > self.durations['maxMvtOnset']:
                self.textToDraw = 'Too late'
            self.sounds['wrong'].play()
        else:
            self.sounds['valid'].play()

        self.trial.stop(self.validTrial)
        self.trial.writedata(self.data)
        self.optotrack.stop_trial(self.trial.id, self.validTrial)

    # =========================================
    # Response
    # =========================================

    def getresponse(self):
        """
        Get response: the user has x seconds maximum to reach to the target.
        :return:
        """
        if self.timers['responseDuration'] is None:
            # Initialize timer
            self.validMvt = False  # Assume the hand movement is not valid
            self.timers['responseDuration'] = time.time()
            self.data['final_hand_position'] = False

        # Time remaining until the end of the response phase
        time_remaining = self.durations['Response'] - (time.time() - self.timers['responseDuration'])

        # Has the hand left the resting position?
        status = self.optotrack.sensors['hand2'].checkposition(self.initHandPosition, self.radiusOff)
        if not status and self.timers['mvtDuration'] is None:
            # If hand has left the homing position, then signal movement onset.
            # Blank out stimuli once the movement has started

            self.optotrack.sendMessage('MOVEMENT_ONSET')
            self.timers['mvtDuration'] = time.time()
            mvt_latency = self.timers['mvtDuration'] - self.timers['responseDuration']
            self.data['mvtLatency'] = round(mvt_latency*1000)
            self.validMvt = self.durations['minMvtOnset'] <= mvt_latency <= self.durations['maxMvtOnset']

        if time_remaining <= 0:
            # If the hand hasn't started to move within the limited response time, then signal a TIMEOUT and end the
            # trial
            self.optotrack.sendMessage('TIMEOUT')
            self.state = "response_off"
            self.changestate()
        else:
            if self.validMvt and self.optotrack.sensors['hand2'].validposition(threshold_time=self.optoTimeThres):
                # If the hand started to move and is valid, then we capture the final hand position and end the trial
                self.data['final_hand_position'] = self.optotrack.sensors['hand2'].position
                self.timers['responseDuration'] = round((time.time() - self.timers['responseDuration'])*1000)
                self.optotrack.sendMessage('MOVEMENT_OFFSET {}'.format(self.optotrack.position2Str(
                    self.data['final_hand_position'])))
                self.timers['mvtDuration'] = round((time.time() - self.timers['mvtDuration'])*1000)
                self.state = "response_off"
                self.changestate()

    def checkposition(self, duration=0.100):
        """
        Check that the tracked hand stays at the resting position before starting the trial.
        :param duration:
        :return:
        """
        if self.PositionChecker is None:
            self.PositionChecker = checkPosition(self.optotrack, self.optotrack.sensors['hand2'], self.initHandPosition,
                                                 self.radiusOn, duration)

        if self.PositionChecker.validateposition():
            self.validTrial = True
            self.state = "stimulus_on"
            self.changestate()

    # =========================================
    # Stereoscopic view
    # =========================================

    def togglestereo(self, on, sim=False):
        """
        Toggle stereoscopic view
        :param on:
        :param sim:
        :return:
        """
        if on or len(self.views) == 1:
            if sim:
                self.views = ('LEFTSIM', 'RIGHTSIM')
            else:
                self.views = ('LEFT', 'RIGHT')
            self.actions['leftAction'].setEnabled(True)
            self.actions['rightAction'].setEnabled(True)
        else:
            self.views = ('ALL',)
            self.actions['leftAction'].setEnabled(False)
            self.actions['rightAction'].setEnabled(False)
        self.update()

    stereoIntensityLevel = 0  # integer -9 -- 9

    def stereointensity(self, level=None, relative=None):
        """
        change the relative intensity of the left eye and right eye image
        """
        if level is not None:
            self.stereoIntensityLevel = level
        elif abs(self.stereoIntensityLevel + relative) < 10:
            self.stereoIntensityLevel += relative
        self.parent().statusBar().showMessage("Stereo intensity: {}".format(self.stereoIntensityLevel))
        self.update()

    # ========================================
    # Stimuli
    # ========================================
    def move(self):
        """
        Update balls position
        """
        for i in range(self.nBalls):
            if i < 2:
                self.stimuli[i].getposition()
            else:
                self.stimuli[i].position = self.stimuli[1].position + np.array((self.landspacing, 0, 0),
                                                                               dtype='float32')

    # =========================================
    # SLED movement
    # =========================================
    def viewermove(self, x, y=None):
        """
        Move the viewer's position
        :param x: horizontal position
        :param y: vertical position
        """
        self.pViewer[0] = x
        self.pViewer[1] = 0
        if y is not None:
            self.pViewer[1] = y
        self.update()
        return self.pViewer

    def getviewerposition(self):
        """
        Get viewer (sled) position
        """
        position = self.sled.getposition()
        self.pViewer = self.viewermove(position[0], position[1])  # use x- and y-coordinate of first marker

    def mouseMoveEvent(self, event):
        """
        React to a moving mouse right button down in the same way we
        would react to a moving target.
        :param event
        """
        if event.buttons() & Qt.RightButton:
            self.viewermove(
                self.dScreen[0] * (event.posF().x() / self.size().width() - .5),
                self.dScreen[1] * (.5 - event.posF().y() / self.size().height())  # mouse y-axis is inverted
            )

    # =========================================
    # OpenGL methods
    # =========================================

    @staticmethod
    def clear_screen():
        """
        Clear the screen
        """
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

    def initializeobjects(self):
        """
        Bind shaders
        :return:
        """
        if self.running:
            # Make stimuli
            self.initstimuli()

            self.objects['ball'] = MyObject(shape='sphere', size=1.0)
            self.objects['ball'].make()

            self.objects['pong'] = MyObject(shape='parallelepiped', size=(1.0, 0.25, 0.25))
            self.objects['pong'].make()

            self.objects['fixation'] = MyObject(shape='cross')
            self.objects['fixation'].make()

            self.objects['line'] = MyObject(shape='line', size=self.width)
            self.objects['line'].make()

        else:
            self.clear_screen()

    def initializeGL(self):
        """
        Initialize Shaders
        """
        # set up the shaders
        self.program = shader.initializeShaders(shader.vs, shader.fs)

        # constant uniforms
        glUniform1f(glGetUniformLocation(self.program, "rBalls"), self.rBalls)

        # dynamic uniforms
        self.MVPLocation = glGetUniformLocation(self.program, "MVP")
        self.nFrameLocation = glGetUniformLocation(self.program, "nFrame")
        self.fadeFactorLocation = glGetUniformLocation(self.program, "fadeFactor")
        self.colorLocation = glGetUniformLocation(self.program, "color")
        self.offsetLocation = glGetUniformLocation(self.program, "offset")

        # attributes
        self.positionLocation = glGetAttribLocation(self.program, 'position')

        glUniform3f(self.colorLocation, 1, 0, 1)
        glUniform1f(self.fadeFactorLocation, self.fadeFactor)

        self.initializeobjects()

    def resizeGL(self, width, height):
        logging.info("resize: {}, {}".format(width, height))
        self.width = width
        self.height = height

    nFramePerSecond = 0  # number of frame in this Gregorian second
    nFrame = 0  # total number of frames
    nSeconds = int(time.time())

    def paintGL(self):

        if int(time.time()) > self.nSeconds:
            self.nSeconds = int(time.time())
            print("fps: {}".format(self.nFramePerSecond), end='\r')
            sys.stdout.flush()
            self.nFramePerSecond = 0
        self.nFramePerSecond += 1

        if self.triggers['updateTrigger']:
            # Update ball position
            self.move()
            # Did the ball crossed the focal point
            depth_ok = self.stimuli[0].position[2] <= self.maxDepth
        else:
            depth_ok = False

        if self.running:
            glUseProgram(self.program)
            glEnable(GL_DEPTH_TEST)  # painters algorithm without this
            glEnable(GL_MULTISAMPLE)  # anti aliasing
            glClearColor(0.0, 0.0, 0.0, 1.0)  # black background

            # Update viewer position
            self.getviewerposition()

            # set uniform variables
            if self.nFrameLocation != -1:
                glUniform1i(self.nFrameLocation, self.nFrame)

            glDrawBuffer(GL_BACK_LEFT)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            for eye in self.views:
                if eye == 'LEFT':
                    x_eye = -self.dEyes / 2
                    intensitylevel = \
                        (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1)[
                            self.stereoIntensityLevel - 10]
                    glUniform3f(self.colorLocation, 0.0, 0.0, 1.0)
                    if not self.format().stereo():
                        # self implemented side-by-side stereo, for instance in sled lab
                        glViewport(0, 0, self.width / 2, self.height)
                elif eye == 'RIGHT':
                    x_eye = self.dEyes / 2
                    intensitylevel = \
                        (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)[
                            self.stereoIntensityLevel - 10]
                    glUniform3f(self.colorLocation, 1.0, 0.0, 0.0)
                    if self.format().stereo():
                        # os supported stereo, for instance nvidia 3d vision
                        glDrawBuffer(GL_BACK_RIGHT)
                        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                    else:
                        # self implemented side-by-side stereo, for instance in sled lab
                        glViewport(self.width / 2, 0, self.width / 2, self.height)
                else:
                    glViewport(0, 0, self.width, self.height)
                    x_eye = 0
                    intensitylevel = 1.0

                # calculate MVP (VP really)
                z = self.pViewer[2]
                mvp = transforms.arjan(self.dScreen[0], self.dScreen[1],
                                       z - self.zNear, z - self.zFocal, z - self.zFar,
                                       self.pViewer[0] + x_eye, self.pViewer[1])
                glUniformMatrix4fv(self.MVPLocation, 1, GL_FALSE, mvp)

                # Draw objects
                if self.triggers['startTrigger'] is True:
                    # Show fixation cross during the hand position validation
                    self.draw_fixation(intensitylevel)

                if self.triggers['stimulusTrigger'] and depth_ok:
                    # Show balls
                    self.draw_objects(intensitylevel)

                    if self.trial.settings['practice']:
                        self.draw_line(intensitylevel)

                if self.triggers['feedback'] is True:
                    # Show correct target position
                    if self.trial.settings['practice'] is True:
                        self.draw_feedback(intensitylevel)
                    else:
                        self.textToDraw = self.feedback.getFeedBack(self.trial.loadData(), self.trial.nplayed)
                        self.draw_text(self.textToDraw)
                else:
                    # Show paddle
                    self.draw_pong(intensitylevel)

            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glUseProgram(0)

        elif self.textToDraw is not None:
            self.draw_text(self.textToDraw)
        else:
            self.clear_screen()

        # Schedule next frame
        self.nFrame += 1
        self.update()  # Draw immediately

    # =========================================
    # Optotrak methods
    # =========================================
    def optorecord(self):
        """
        Record hand movements
        :return:
        """
        # if self.timerRecord is None:
        #     self.timerRecord = time.time()
        # elapsedTime = time.time() - self.timerRecord
        # self.timerRecord = time.time()
        # print('Optorecord: {} s'.format(elapsedTime))

        if self.optotrack.running and self.running:
            recorded = self.optotrack.recordPosition()
            if recorded:
                # Record stimuli position
                sled_position = self.pViewer
                str_pos_land1 = self.optotrack.position2Str(self.stimuli[1].position)
                str_pos_land2 = self.optotrack.position2Str(self.stimuli[2].position)
                str_pos_target = self.optotrack.position2Str(self.stimuli[0].position)
                pong_position = self.optotrack.position2Str(self.pong_position)
                self.optotrack.sendMessage('STIM Sled {} Land1 {} Target {} Land2 {} Pong {}'
                                           .format(sled_position[0], str_pos_land1, str_pos_target, str_pos_land2,
                                                   pong_position))
            if self.triggers['startTrigger']:
                self.checkposition(self.optoTimeThres)
            elif self.triggers['checkTrigger']:
                self.validTrial = self.optotrack.sensors['hand2'].checkposition(self.initHandPosition, self.radiusOn)
            elif self.triggers['responseTrigger']:
                self.getresponse()

    # =========================================
    # Drawing methods
    # =========================================

    def draw_objects(self, intensitylevel):
        """
        Draw objects
        :param intensitylevel
        :return:
        """
        # enable vertex attributes used in both balls and fixation cross
        glEnableVertexAttribArray(self.positionLocation)

        self.objects['ball'].vertices.bind()
        self.objects['ball'].indices.bind()
        glVertexAttribPointer(self.positionLocation, 3, GL_FLOAT, False, 3 * 4, self.objects['ball'].vertices)

        if self.predict is False:
            nballs = 1
        else:
            nballs = self.nBalls

        for i in range(nballs):  # change ball color depending on state, maybe put in function later
            if self.triggers['targetVisible'] is False and i == 0:
                # Do not draw the target
                continue
            # draw stimuli as elements (with indices)
            glUniform3fv(self.colorLocation, 1, intensitylevel * self.stimuli[i].color)
            glUniform3fv(self.offsetLocation, 1, self.stimuli[i].position)
            glDrawElements(GL_TRIANGLES, self.objects['ball'].indices.data.size, GL_UNSIGNED_INT,
                           self.objects['ball'].indices)

        self.objects['ball'].vertices.unbind()
        self.objects['ball'].indices.unbind()

        glDisableVertexAttribArray(self.positionLocation)

    def draw_feedback(self, intensitylevel):
        """
        Draw the expected target location and the final hand position (feedback)
        :param intensitylevel
        :return:
        """
        # enable vertex attributes used in both balls and fixation cross
        glEnableVertexAttribArray(self.positionLocation)

        # Draw the correct target location
        self.objects['ball'].vertices.bind()
        self.objects['ball'].indices.bind()
        glVertexAttribPointer(self.positionLocation, 3, GL_FLOAT, False, 3 * 4, self.objects['ball'].vertices)

        # draw stimuli as elements (with indices)
        glUniform3fv(self.colorLocation, 1, intensitylevel * np.array((0.0, 1.0, 0.0), dtype='float32'))
        glUniform3fv(self.offsetLocation, 1, self.data['requested_target_position'])
        glDrawElements(GL_TRIANGLES, self.objects['ball'].indices.data.size, GL_UNSIGNED_INT,
                       self.objects['ball'].indices)

        self.objects['ball'].vertices.unbind()
        self.objects['ball'].indices.unbind()

        # Draw the final hand location
        self.objects['pong'].vertices.bind()
        self.objects['pong'].indices.bind()
        glVertexAttribPointer(self.positionLocation, 3, GL_FLOAT, False, 3*4, self.objects['pong'].vertices)

        # draw stimuli as elements (with indices)
        glUniform3fv(self.colorLocation, 1, intensitylevel * np.array([1, 1, 1], 'f'))
        glUniform3fv(self.offsetLocation, 1, self.pong_position)

        glDrawElements(GL_TRIANGLES, self.objects['pong'].indices.data.size, GL_UNSIGNED_INT,
                       self.objects['pong'].indices)
        self.objects['pong'].vertices.unbind()
        self.objects['pong'].indices.unbind()

        glDisableVertexAttribArray(self.positionLocation)

    def draw_fixation(self, intensitylevel):
        """
        Build a fixation cross centered on a given horizontal position
        :param intensitylevel
        :return:
        """

        fixation_x = self.pViewer[0] + self.homePosition

        # Enable vertex attributes used in both balls and fixation cross
        glEnableVertexAttribArray(self.positionLocation)

        # Hand position in normalized coordinates
        self.objects['fixation'].vertices.bind()
        self.objects['fixation'].indices.bind()
        glVertexAttribPointer(self.positionLocation, 3, GL_FLOAT, False, 3*4, self.objects['fixation'].vertices)

        # draw stimuli as elements (with indices)
        glUniform3fv(self.colorLocation, 1, intensitylevel * np.array([1, 0, 0], 'f'))
        glUniform3fv(self.offsetLocation, 1, np.array([fixation_x, self.landingLimit, self.maxDepth], dtype='float32'))

        glDrawElements(GL_TRIANGLES, self.objects['fixation'].indices.data.size, GL_UNSIGNED_INT,
                       self.objects['fixation'].indices)
        self.objects['fixation'].vertices.unbind()
        self.objects['fixation'].indices.unbind()

        glDisableVertexAttribArray(self.positionLocation)

    def draw_line(self, intensitylevel):
        """
        Draw landing line
        :param intensitylevel
        :return:
        """
        glEnableVertexAttribArray(self.positionLocation)

        self.objects['line'].vertices.bind()
        self.objects['line'].indices.bind()
        glVertexAttribPointer(self.positionLocation, 3, GL_FLOAT, False, 3*4, self.objects['line'].vertices)

        # draw stimuli as elements (with indices)
        glUniform3fv(self.colorLocation, 1, intensitylevel * np.array([1, 1, 1], 'f'))
        glUniform3fv(self.offsetLocation, 1, np.array([0, self.landingLimit, self.maxDepth], dtype='float32'))

        glDrawElements(GL_LINES, self.objects['line'].indices.data.size, GL_UNSIGNED_INT,
                       self.objects['line'].indices)
        self.objects['line'].vertices.unbind()
        self.objects['line'].indices.unbind()

    def draw_text(self, txt, x=0.0, y=0.0, z=0.0, font_name='Arial', size=25):
        """
        Draw text at a given position
        :param txt: string
        :param x: float
        :param y: float
        :param z: float
        :param font_name: name of the font
        :param size: font size
        :return:
        """

        # Clear screen and unbind buffer
        glUseProgram(0)

        glClearColor(0.0, 0.0, 0.0, 1.0)  # Background color
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glColor3f(1.0, 1.0, 1.0)  # Font color

        # Render text
        txt = QString(txt)
        font = QFont(font_name, size, QFont.Light)
        self.renderText(x, y, z, txt, font)

    def draw_pong(self, intensitylevel):
        """
        Draw a rectangle at a specified location
        :param intensitylevel:
        :return:
        """
        # Enable vertex attributes used in both balls and fixation cross
        glEnableVertexAttribArray(self.positionLocation)

        # Hand position in normalized coordinates
        hand_position = self.optotrack.sensors['hand2'].position
        homingPosition = self.sledCenter

        if not self.trial.settings['optotrack']:
            pong_position = self.pViewer[0]+(float(hand_position[0])/float(self.width)-0.5)
        else:
            hand_to_center = (hand_position[0] - homingPosition[0])
            pong_position = self.pViewer[0] + hand_to_center

        self.pong_position = np.array([pong_position, self.landingLimit, self.maxDepth], dtype='float32')

        self.objects['pong'].vertices.bind()
        self.objects['pong'].indices.bind()
        glVertexAttribPointer(self.positionLocation, 3, GL_FLOAT, False, 3*4, self.objects['pong'].vertices)

        # draw stimuli as elements (with indices)
        glUniform3fv(self.colorLocation, 1, intensitylevel * np.array([1, 1, 1], 'f'))
        glUniform3fv(self.offsetLocation, 1, self.pong_position)

        glDrawElements(GL_TRIANGLES, self.objects['pong'].indices.data.size, GL_UNSIGNED_INT,
                       self.objects['pong'].indices)
        self.objects['pong'].vertices.unbind()
        self.objects['pong'].indices.unbind()

        glDisableVertexAttribArray(self.positionLocation)
