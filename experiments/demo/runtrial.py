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

# Import libraries
#################################
# DO NOT MODIFY THE LINES BELOW #
#################################
from __future__ import print_function
from __future__ import division

# psychopy
# Use pyo library instead of pygame
from psychopy import prefs
prefs.general['audioLib'] = ['pygame']
from psychopy import visual, sound
import pygame
import time
import numpy as np

# EasyExp modules
from core.Core import Core
from core.movie.moviemaker import MovieMaker
from core.buttons.buttons import UserInput
from core.display.fpscounter import FpsCounter
from core.events.timer import Timer

# Multi-threading
import threading

#################################
# ADD YOUR CUSTOM IMPORTS BELOW #
#################################
from core.misc.conversion import pol2cart, mm2pix, deg2m
from core.apparatus.sled.sled import Sled
from core.apparatus.eyetracker.eyetracker import EyeTracker


class RunTrial(object):
    """
    RunTrial class
    This class handles experiment's trials procedure

    This class calls on two state machines, one fast (close to real-time), one slow (limited by screen's refresh rate)
    A same state can be present in both state machines, but it should only call rendering operation within the slow
    state machine
    For instance, if you want to record hand movement while displaying a stimulus on the screen, the rendering
    operations should be implemented in RunTrial::graphics_state_machine(), whereas the recording of hand positions
    should be coded in the fast_state_machine().

    IMPORTANT:
    The actual multi-threading implementation of this class is not perfectly thread-safe. For that reason, the two
    state machines should be considered independent from each other and should not make operation on shared variables.
    However, because the fast state machine runs much faster than the graphics state machine, then changes made within
    the fast state machine will be accessible by the slowest state machine, BUT NOT NECESSARILY THE OTHER WAY AROUND!
    Therefore, if objects have to be modified within a thread, this should be done in the fastest one.

    API
    - RunTrial.__init__(): Class's constructor. Triggers and data field can be initialized here. In general,
    any variables used by several class' methods should be initialized in the constructor as self._attribute_name
    - RunTrial.init_devices(): devices used by the experiment should be instantiated here.
    - RunTrial.init_trial(): Initialization of trial (get trial's information, reset triggers and data). This method
    should not be modified
    - RunTrial.init_stimuli(): Initialization/Preparation of stimuli. Creation of stimuli objects should be implemented
    here.
    - RunTrial.init_audio(): Initialization/Preparation of auditory stimuli and beeps. Creation of auditory objects
    should be implemented here.
    - RunTrial.quit(): Quit experiment. This method is called when the experiment is over (no more trials to be played)
    or when the user press the "quit" key.
    - RunTrial.go_next(): Check if transition to next state is requested (by key press or timer)
    - RunTrial.get_response(): Participant's response should be handled here. This method is typically called during the
    "response" state.
    - RunTrial.end_trial(): End trial routine. Write data into file and check if the trial is valid or invalid.
    - RunTrial.getviewerposition(): Get sled (viewer) position. This method is called by the fast state machine.
    - RunTrial.run(): Application's main loop.
    - RunTrial.change_state(): handles transition between states.
    - RunTrial.fast_state_machine(): Real-time state machine.
    - RunTrial.graphics_state_machine(): Slow state machine.
    """

    homeMsg = 'Welcome!'  # Message prompted at the beginning of the experiment

    def __init__(self, exp_core=Core):
        """
        Class constructor

        Parameters
        ----------
        :param Core exp_core: Core object
        :type exp_core: Core
        """

        ##################################
        # DO NOT MODIFY THE LINES BELLOW #
        ##################################
        # super(RunTrial, self).__init__(core=core)

        self.core = exp_core
        self.screen = exp_core.screen
        self.trial = exp_core.trial
        self.user = exp_core.user
        self.ptw = self.screen.ptw
        self.textToDraw = RunTrial.homeMsg

        # State Machine
        # =============
        self.state_machine = {
            'current': None,
            'status': False,
            'singleshot': True,
            'timer': None,
            'duration': 0.0,
            'onset': 0.0,
            'offset': 0.0
        }
        self.status = True
        self.state = 'idle'
        self.nextState = "iti"
        self.validTrial = False

        # Dependencies
        # ============
        # FPScounter: measures flip duration or simply flips the screen
        self.fpsCounter = FpsCounter(self.screen.ptw)

        # Logger: verbose level can be set by changing level to 'debug', 'info' or 'warning'
        self.logger = exp_core.logger

        # Stimuli
        # =======
        self.stimuli = dict()

        # Devices
        # =======
        self.devices = dict()
        # Setup devices
        self.init_devices()

        # Audio/Video
        # ===========
        # Initialize audio
        self.sounds = dict()
        self.init_audio()
        self.movie = None

        # Timings
        # =======
        self.timings = self.trial.parameters['durations']

        ################################
        # LINES BELOW CAN BE MODIFIED #
        ################################
        # Experiment settings
        # ===================
        # Experiment's parameters can accessed by calling self.trial.parameters['parameter_name']
        # Because parameters are loaded from a JSON file, they are imported as string. Therefore, it might be necessary
        # to convert the parameter's type: e.g. as a float number.
        # Example:
        # my_parameter = float(self.trial.parameters['my_parameter']

        # Sled settings
        self.pViewer = [0.0, 0.0]
        self.mvtBackDuration = float(self.trial.parameters['mvtBackDuration'])  # Returning movement duration (in s)
        self.sledHome = 0.0  # Sled home position
        self.sledStart = float(self.trial.parameters['sledStart'])  # Sled starting position
        self.mvtAmplitude = float(self.trial.parameters['movDistance'])  # Movement amplitude
        self.mvtDuration = float(self.trial.parameters['movDuration'])  # Movement duration (in s)
        self.sledFinal = 0.0  # Sled final position (trial parameter)

        # Events triggers
        # ===============
        # Default triggers are moveOnRequested, pauseRequested, startTrigger and quitRequested.
        # They should not be modified. However, you can add new triggers: 'trigger_name': False
        self.triggers = {
            'moveOnRequested': False,
            'pauseRequested': False,
            'startTrigger': False,
            'response_given': False,
            'quitRequested': False
        }

        # Add your stimulus trigger to this dictionary. If self.stimuliTrigger['stimulus_name'] = True,
        # then self.stimuli['stimulus_name'].draw() will be called.
        self.stimuliTrigger = {
            'probe1': False,
            'probe2': False,
            'fixation': False
        }

        # Timers
        # ======
        # Add your timers to this dictionary.
        # Default timer is timers['runtime'] and it should not be removed
        #
        # Example:
        # timers = {'timer_name': Timer()}
        #
        # Then, to start the timer
        # timers['timer_name'].start()
        #
        # Stop the timer
        # timers['timer_name'].stop()
        #
        # Get elapsed time
        # print(timers['timer_name'].get_time('elapsed')
        #
        # Reset timer
        # timers['timer_name'].reset()

        self.timers = {
            'runtime': Timer(),  # DO NOT MODIFY
            'sled_start': Timer(),
            'responseDuration': Timer()
        }

        # Data
        # ====
        # Data field that will be output into the data file should be specified here.
        self.data = {
            'probe1': None,
            'probe2': None,
            'intensity': None,
            'response': None,
            'correct': None,
            'responseDuration': None,
            'sled_probe1': None,
            'sled_probe2': None,
            'time_probe1': None,
            'time_probe2': None
        }

        # Keyboard/Mouse Inputs
        # Calls UserInput observer
        # Usage:
        # # Create instance
        # Inputs = UserInput()
        # Inputs.add_device('keyboard')  # arguments are (device type, device arguments: optional)
        # Inputs.add_device('mouse', visible=False, newPos=None, win=win)
        #
        # # Add listeners
        # Inputs.add_listener('keyboard', 'a', K_a)  # arguments are: device_type, key label, key code (Pygame constant)
        # Inputs.add_listener('keyboard', 'quit', K_ESCAPE)
        # Inputs.add_listener('mouse', 'left', 0)
        #
        # Update status
        # Inputs.update()

        # Access watched key's status
        # Inputs.get_status('a')  # returns True or False
        # ================
        self.buttons = UserInput()
        # Input devices used in the experiment
        self.buttons.add_device('keyboard')
        self.buttons.add_device('mouse', visible=False, newPos=None, win=self.ptw)

        # GUI related keys
        # quit, pause and move on keys must be specified
        self.buttons.add_listener('keyboard', 'pause', pygame.K_SPACE)
        self.buttons.add_listener('keyboard', 'quit', pygame.K_q)
        self.buttons.add_listener('mouse', 'move_on', 0)

        # Response keys
        # Add your response keys below
        self.buttons.add_listener('mouse', 'left', 0)
        self.buttons.add_listener('mouse', 'right', 2)

        # Staircase
        # =========
        from core.methods.StaircaseASA.StaircaseASA import StaircaseASA
        self.staircase = StaircaseASA(settings_file=self.trial.design.conditionFile.pathtofile,
                                      data_file=self.user.datafilename)

    # =========================================
    # SLED movement
    # =========================================
    def getviewerposition(self):
        """
        Get viewer (sled) position
        """
        p = self.devices['sled'].getposition(t=self.devices['sled'].client.time())
        self.pViewer = (p[0], p[1])

    # =========================================
    # STATE MACHINE
    # =========================================

    def run(self):
        """
        Application main loop
        DO NOT MODIFY
        """
        t1 = threading.Thread(target=self.fast_state_machine)
        t1.start()
        while self.status:
            self.graphics_state_machine()

        t1.join()

    def change_state(self):
        """
        This function handles transition between states
        DO NOT MODIFY
        :rtype: bool
        """
        if self.timers['runtime'] is None or self.timers['runtime'].get_time('start') is None:
            self.timers['runtime'] = Timer()
            self.timers['runtime'].start()

        if self.state_machine['current'] is None:
            # If we enter a new state
            self.state_machine['current'] = self.state
            self.state_machine['timer'] = Timer(max_duration=self.timings[self.state])
            self.state_machine['timer'].start()
            self.state_machine['onset'] = self.state_machine['timer'].get_time('start')
            self.state_machine['status'] = True
            self.triggers['moveOnRequested'] = False
            self.state_machine['singleshot'] = True  # Enable single shot events

            # Send events to devices that will be written into their data file
            for device in self.devices:
                if hasattr(self.devices[device], 'send_message'):
                    self.devices[device].send_message('EVENT_STATE_{}'.format(self.state))

        # Check inputs and timers
        self.triggers['moveOnRequested'] = self.go_next() if self.triggers['moveOnRequested'] is False else True

        # If we transition to the next state
        if self.triggers['moveOnRequested'] and self.state_machine['status']:
            self.state_machine['timer'].stop()
            self.state_machine['offset'] = self.state_machine['timer'].get_time('stop')
            self.state_machine['duration'] = self.state_machine['timer'].get_time('elapsed')
            self.state_machine['timer'].reset()

            state_str = '[STATE]: {0}=>{1}' \
                        ' [START: {2:.3f}s | DUR: {3:.3f}s]'.format(self.state, self.nextState,
                                                                    self.state_machine['onset'] -
                                                                    self.timers['runtime'].get_time('start'),
                                                                    self.state_machine['duration'])
            self.logger.logger.info(state_str)

            self.state = self.nextState
            self.triggers['moveOnRequested'] = False
            self.state_machine['status'] = False
            self.state_machine['current'] = None
            return True
        else:
            return False

    def quit(self):
        """
        Quit experiment
        :return:
        """
        # Set in idle mode
        self.state = 'idle'
        self.textToDraw = "Experiment is over!"

        # Shutdown devices
        for device in self.devices:
            if hasattr(self.devices[device], "close"):
                self.logger.logger.info('[{}] Closing "{}"'.format(__name__, device))
                self.devices[device].close()

        self.status = False

    def go_next(self):
        """
        Check if it is time to move on to the next state. State changes can be triggered by key press (e.g.: ESCAPE key)
        or timers. States' duration can be specified in the my_project_name/experiments/experiment_name/parameters.json
        file.
        :rtype: bool
        """
        # Update input devices state
        self.buttons.update()

        # Does the user want to quit the experiment?
        if self.buttons.get_status('quit'):
            self.triggers['quitRequested'] = True

        # Does the user want a break?
        if self.buttons.get_status('pause'):
            self.triggers['pauseRequested'] = True

        # Shall we go on?
        if self.timings[self.state] is not False:
            timeToMoveOn = (time.time() - self.state_machine['onset']) >= self.timings[self.state]
        else:
            timeToMoveOn = self.buttons.get_status('move_on')

        return timeToMoveOn

    def init_trial(self):
        """
        Initializes trial
        Check if we should start a new trial, trigger a pause or quit the experiment
        DO NOT MODIFY

        :return void:
        """
        # Check experiment status
        status = self.trial.setup()
        if status is False:
            # If no more trials to run, then quit the experiment
            self.nextState = 'quit'
            self.triggers['moveOnRequested'] = True
            return False
        else:
            self.status = status
            if self.status is "pause":
                self.triggers['pauseRequested'] = True
                self.nextState = 'pause'
                self.triggers['moveOnRequested'] = True
                return 'pause'

            # Start a new trial
            # Reset timers
            for timer, value in self.timers.iteritems():
                self.timers[timer].reset()

            # Reset data
            for data, value in self.data.iteritems():
                self.data[data] = None

            # Reset stimuli triggers
            for label, value in self.stimuliTrigger.iteritems():
                self.stimuliTrigger[label] = False

            # Reset event triggers
            for label, value in self.triggers.iteritems():
                self.triggers[label] = False

            # Send START_TRIAL to devices
            for device in self.devices:
                if hasattr(self.devices[device], 'start_trial'):
                    self.devices[device].start_trial(self.trial.id, self.trial.params)

            # Initialize movie if requested
            if self.trial.settings['setup']['movie']:
                self.movie = MovieMaker(self.ptw, "Dynamic_{}_{}".format(self.trial.params["first"],
                                                                         self.trial.params['timing']), "png")
            # Initialize stimuli
            self.init_stimuli()

            return True

    def end_trial(self):
        """
        End trial routine
        :return:
        """
        # Did we get a response from the participant?
        self.validTrial = self.triggers['response_given'] is not False
        self.timers['runtime'].reset()

        # Close movie file is necessary
        if self.trial.settings['setup']['movie']:
            self.movie.close()

        # Replay the trial if the user did not respond fast enough or moved the hand before the response phase
        self.logger.logger.debug('[{}] Trial {} - Results:'.format(__name__, self.trial.id))
        for data, value in self.data.iteritems():
            self.logger.logger.debug('[{}] {}: {}'.format(__name__, data, value))
        self.logger.logger.info('[{}] Trial {} - Valid: {}'.format(__name__, self.trial.id, self.validTrial))

        # Play an auditory feedback to inform whether the trial was valid or not
        if not self.validTrial:
            self.sounds['wrong'].play()
        else:
            self.sounds['valid'].play()

        self.trial.stop(self.validTrial)  # Stop routine
        self.trial.writedata(self.data)  # Write data

        # Call closing trial routine
        for device in self.devices:
            if hasattr(self.devices[device], "stop_trial"):
                self.devices[device].stop_trial(self.validTrial)

    ################################
    # CUSTOMIZATION STARTS HERE    #
    ################################

    def init_devices(self):
        """
        Setup devices
        For better readability of the code, devices should be added to self.devices dictionary.
        RunTrial calls some devices methods automatically if the device's class has such methods:
        - Device::close(): this method should implement the closing method of the device. If does not take arguments.
        - Devices::start_trial(trial_id, trial_parameters): routine called at the begining of a trial. Parameters are:
            int trial_id: trial number (or unique id)
            dict trial_parameters: Trial.params
        - Devices::stop_trial(trial_id, valid_trial): routine called at the end of a trial. Parameters should be:
            int trial_id: trial number (or unique id)
            bool valid_trial: is it a valid trial or not (e.g.: should it be excluded from analysis).
        """
        # Create Sled instance
        self.devices['sled'] = Sled(dummy_mode=not self.trial.settings['devices']['sled'], server='sled')

        # Create eye-tracker instance
        if self.trial.settings['devices']['eyetracker']:
            user_file = "{}_{}_{}".format(self.user.dftName, 'eyetracker', time.strftime('%d-%m-%Y_%H%M%S'))
            self.devices['eyetracker'] = EyeTracker(link='10.0.0.20', dummy_mode=False, sprate=500, thresvel=35,
                                                    thresacc=9500, illumi=2, caltype='HV5', dodrift=False,
                                                    trackedeye='right', display_type='psychopy', user_file=user_file,
                                                    ptw=self.ptw, bgcol=(-1, -1, -1), distance=self.screen.distance,
                                                    resolution=self.screen.resolution,
                                                    winsize=self.screen.size, inner_tgcol=(127, 127, 127),
                                                    outer_tgcol=(255, 255, 255), targetsize_out=1.0, targetsize_in=0.25)
            self.devices['eyetracker'].run()
            self.state = 'calibration'

    def init_audio(self):
        """
        Initialize sounds
        Auditory stimuli are created here and should be stored in RunTrial.sounds dictionary. For example:
        self.sounds['stimulus_name'] = sound.SoundPygame(secs=0.1, values=880)

        Then you can play the sound by calling:
        self.sounds['stimulus_name'].play()

        :return:
        """
        # Sound
        self.sounds['valid'] = sound.Sound(secs=0.1, value=880)
        self.sounds['valid'].setVolume(1)

        self.sounds['wrong'] = sound.Sound(secs=0.1, value=440)
        self.sounds['wrong'].setVolume(1)

    def init_stimuli(self):
        """
        Prepare/Make stimuli

        Stimuli objects (Psychopy) should be stored in self.stimuli dictionary, for example:
        self.stimuli['stimulus_name'] = visual.Circle(self.ptw, radius=2, pos=(0, 0))

        Then on every loop, the state machine will automatically call self.stimuli['stimulus_name'].draw() if
        self.stimuliTrigger['stimulus_name'] is set to True.
        """
        # Get new stimulus intensity estimated by staircase method
        self.data['intensity'] = self.staircase.update(int(self.trial.params['staircaseID']),
                                                       int(self.trial.params['staircaseDir']))

        # Probe size
        probeSizeM = deg2m(float(self.trial.parameters['probeSize']), self.screen.distance/1000.0)*1000.0
        probeSize = 0.5*mm2pix(probeSizeM, probeSizeM, self.screen.resolution, self.screen.size)  # Radius in pixels

        # Top probe location
        probe1PosM = deg2m(float(self.data['intensity']), self.screen.distance/1000.0)*1000.0
        probeTopPos = mm2pix(probe1PosM, float(self.trial.parameters['probeTop']), self.screen.resolution,
                             self.screen.size)

        # bottom probe location
        probeBottomPos = mm2pix(-probe1PosM, float(self.trial.parameters['probeBottom']), self.screen.resolution,
                                self.screen.size)

        # Fixation point
        fixationSizeM = deg2m(float(self.trial.parameters['fixationSize']), self.screen.distance/1000.0)*1000.0
        fixation = 0.5 * mm2pix(fixationSizeM, fixationSizeM, self.screen.resolution, self.screen.size)

        fillColor = (-0.7, -0.7, -0.7)  # Probe fill color: Mid gray
        lineColor = (-0.7, -0.7, -0.7)  # Probe line color: Mid gray

        # Make stimuli
        if self.trial.params['first'] == 'top':
            self.data['probe1'] = probe1PosM  # Save probe coordinates in mm
            self.data['probe2'] = -probe1PosM  # Save probe coordinates in mm
            probe1Pos = probeTopPos
            probe2Pos = probeBottomPos
        else:
            self.data['probe1'] = -probe1PosM  # Save probe coordinates in mm
            self.data['probe2'] = probe1PosM  # Save probe coordinates in mm
            probe1Pos = probeBottomPos
            probe2Pos = probeTopPos

        self.stimuli['probe1'] = visual.Circle(self.ptw, radius=probeSize[0], pos=probe1Pos, lineWidth=1,
                                               lineColor=lineColor, fillColor=fillColor, units='pix')
        self.stimuli['probe2'] = visual.Circle(self.ptw, radius=probeSize[0], pos=probe2Pos, lineWidth=1,
                                               lineColor=lineColor, fillColor=fillColor, units='pix')
        self.stimuli['fixation'] = visual.Circle(self.ptw, radius=fixation[0], pos=(0.0, 0.0), lineWidth=1,
                                                 lineColor=(-0.7, -0.7, -0.7), fillColor=(-0.7, -0.7, -0.7),
                                                 units='pix')

    def get_response(self):
        """
        Get participant' response
        """
        # Initialize response timer
        if self.timers['responseDuration'] is None or self.timers['responseDuration'].get_time('start') is None:
            self.timers['responseDuration'] = Timer()
            self.timers['responseDuration'].start()

        # Get response buttons status
        response_received = self.buttons.get_status('left') or self.buttons.get_status('right')

        if not self.triggers['response_given'] and response_received:
            self.triggers['response_given'] = True

            # Stop response timer, store response duration, and reset timer
            self.timers['responseDuration'].stop()
            self.data['responseDuration'] = round(self.timers['responseDuration'].get_time('elapsed')*1000.0)
            self.timers['responseDuration'].reset()

            # Code response
            self.data['response'] = 'left' if self.buttons.get_status('left') else 'right'
            self.data['correct'] = self.data['response'] == 'right'

    def fast_state_machine(self):
        """
        Real-time state machine: state changes are triggered by keys or timers. States always have the same order.
        This state machine runs at close to real-time speed. Event handlers (key press, etc.) and position trackers
        (optotrak, eye-tracker or sled) should be called within this state machine.
        Rendering of stimuli should be implemented in the graphics_state_machine()
        """
        while self.status:

            ################################
            # DO NOT MODIFY THE LINE BELOW #
            ################################

            # Check state status
            self.change_state()

            # Get sled (viewer) position
            self.getviewerposition()

            if self.state == 'idle':
                # IDLE state
                # DO NOT MODIFY
                self.nextState = 'iti'

            elif self.state == 'quit':
                # QUIT experiment
                # DO NOT MODIFY

                if self.state_machine['singleshot']:
                    self.state_machine['singleshot'] = False
                    self.quit()

            elif self.state == 'pause':
                # PAUSE experiment
                # DO NOT MODIFY
                self.nextState = 'iti'
                if self.state_machine['singleshot']:
                    self.state_machine['singleshot'] = False
                    self.triggers['pauseRequested'] = False

                    # Move the sled back to its default position
                    if 'sled' in self.devices and self.devices['sled'] is not None:
                        self.devices['sled'].move(self.sledHome, self.mvtBackDuration)
                        time.sleep(self.mvtBackDuration)
                        self.devices['sled'].lights(True)  # Turn the lights off

            elif self.state == 'calibration':
                # Eye-tracker calibration
                self.nextState = 'iti'

            elif self.state == 'iti':
                # Inter-trial interval
                self.nextState = 'start'
                if self.state_machine['singleshot']:
                    self.state_machine['singleshot'] = False
                    if self.devices['sled'] is not None:
                        self.devices['sled'].lights(False)  # Turn the lights off

            elif self.state == 'start':
                # Start trial: get trial information and update trial's parameters accordingly
                self.nextState = 'first'

                if self.state_machine['singleshot'] is True:
                    # DO NOT MODIFY THE LINES BELOW
                    self.state_machine['singleshot'] = False
                    status = self.init_trial()  # Get trial parameters
                    if not status:
                        self.nextState = 'quit'
                        self.triggers['moveOnRequested'] = True
                    if status is 'pause':
                        self.nextState = 'pause'
                        self.triggers['moveOnRequested'] = True

                        self.data['response'] = False

                    # ADD YOUR CODE HERE
                    # Self motion settings
                    side = 1 if self.trial.params['side'] == 'right' else -1
                    self.sledStart = side * float(self.trial.parameters['sledStart'])  # Sled homing position (in m)
                    self.mvtAmplitude = float(self.trial.parameters['movDistance'])
                    self.sledFinal = self.sledStart + side * self.mvtAmplitude  # Final sled position

                    # Stimuli Triggers
                    self.triggers['startTrigger'] = True
                    self.stimuliTrigger['fixation'] = True

                    # Compute states duration
                    screen_latency = 0.050  # Screen latency in ms
                    self.timings['first'] = float(self.trial.params['timing']) - screen_latency
                    self.timings['probe1'] = float(self.trial.parameters['probeDuration'])
                    self.timings['probeInterval'] = float(self.trial.parameters['probeInterval'])
                    self.timings['probe2'] = self.timings['probe1']
                    self.timings['last'] = 0.0

                    # Move sled to starting position if it is not there already
                    if np.abs(self.pViewer[0] - self.sledStart) > 0.01:
                        self.logger.logger.debug(
                            'Sled is not at starting position: {} instead of {}'.format(self.pViewer[0],
                                                                                        self.sledStart))
                        self.devices['sled'].move(self.sledStart, self.mvtBackDuration)
                        self.timings['start'] = self.mvtBackDuration + 0.1
                        time.sleep(self.mvtBackDuration)
                        self.getviewerposition()  # Get SLED's position
                        self.logger.logger.debug('Sled after move command: {}'.format(self.pViewer[0]))

                    else:
                        self.timings['start'] = 0.1

            elif self.state == 'first':
                self.nextState = 'probe1'
                if self.state_machine['singleshot'] is True:
                    self.state_machine['singleshot'] = False
                    self.timers['sled_start'].start()
                    self.devices['sled'].move(self.sledFinal, self.mvtDuration)

            elif self.state == 'probe1':
                self.nextState = 'probeInterval'
                self.stimuliTrigger['probe1'] = True
                if self.state_machine['singleshot'] is True:
                    self.state_machine['singleshot'] = False
                    self.data['sled_probe1'] = self.pViewer[0]
                    self.data['time_probe1'] = self.timers['sled_start'].get_time('elapsed')

            elif self.state == 'probeInterval':
                self.nextState = 'probe2'
                self.stimuliTrigger['probe1'] = False

            elif self.state == 'probe2':
                self.nextState = 'last'
                self.stimuliTrigger['probe2'] = True
                if self.state_machine['singleshot'] is True:
                    self.state_machine['singleshot'] = False
                    self.data['sled_probe2'] = self.pViewer[0]
                    self.data['time_probe2'] = self.timers['sled_start'].get_time('elapsed')

            elif self.state == 'last':
                self.nextState = 'response'
                self.stimuliTrigger['probe2'] = False

            elif self.state == 'response':
                self.nextState = 'end'

                # Get participant's response
                self.get_response()

                # If we got a response before the end of the sled's displacement, then wait until the sled has arrived,
                # or move directly to next state
                if self.triggers['response_given']:
                    if self.trial.params['mvt'] == 'True':
                        if self.timers['sled_start'].get_time('elapsed') >= self.trial.parameters['movDuration']:
                            self.triggers['moveOnRequested'] = True
                    else:
                        self.triggers['moveOnRequested'] = True

            elif self.state == 'end':
                # End of trial. Call ending routine.
                if self.triggers['pauseRequested']:
                    self.nextState = "pause"
                elif self.triggers['quitRequested']:
                    self.nextState = "quit"
                else:
                    self.nextState = 'iti'

                if self.state_machine['singleshot'] is True:
                    self.state_machine['singleshot'] = False
                    self.triggers['startTrigger'] = False

                    # End trial routine
                    self.end_trial()

    def graphics_state_machine(self):
        """
        Graphical (slow) state machine: running speed of this state machine is limited by the screen's refresh rate. For
        instance, this state machine will be updated every 17 ms with a 60Hz screen. For this reason, only slow events
        (display of stimuli) should be described here. Everything that requires faster (close to real-time) processing
        should be specified in the RunTrial::fast_state_machine() method.

        Returns
        -------

        """
        if self.state == 'idle':
            text = visual.TextStim(self.ptw, pos=(0.0, 0.0), text=self.textToDraw, units="pix")
            text.draw()

        elif self.state == 'pause':
            text = 'PAUSE {0}/{1} [Replayed: {2}]'.format(self.trial.nplayed, self.trial.ntrials,
                                                          self.trial.nreplay)
            text = visual.TextStim(self.ptw, pos=(0, 0), text=text, units="pix")
            text.draw()

        elif self.state == 'calibration':
            self.nextState = 'iti'
            if self.state_machine['singleshot']:
                self.state_machine['singleshot'] = False
                # Create calibration points (polar grid, with points spaced by 45 degrees)
                x, y = pol2cart(0.25 * (self.screen.resolution[0] / 2), np.linspace(0, 2 * np.pi, 9))
                x += 0.5 * self.screen.resolution[0]  # Center coordinates on screen center
                y += 0.5 * self.screen.resolution[1]

                # Start calibration
                self.devices['eyetracker'].calibration.custom_calibration(x=x, y=y, ctype='HV9')
                self.devices['eyetracker'].calibration.calibrate()

        elif self.state == 'end':
            if self.state_machine['singleshot'] is True:
                self.state_machine['singleshot'] = False

        # Update fixation position (body-fixed)
        if self.triggers['startTrigger']:
            fixation_position = mm2pix(1000 * self.pViewer[0], 0.0, self.screen.resolution, self.screen.size)
            self.stimuli['fixation'].setPos(fixation_position)  # Update fixation position

        ##################################
        # DO NOT MODIFY THE LINES BELLOW #
        ##################################
        # Draw stimuli
        if self.triggers['startTrigger']:
            for stim, status in self.stimuliTrigger.iteritems():
                if stim in self.stimuli:
                    if status:
                        self.stimuli[stim].draw()
                else:
                    msg = Exception('Stimulus "{}" has been initialized in RunTrial::init_stimuli() method!'.format(
                        stim))
                    self.logger.logger.critical(msg)
                    raise msg
        else:
            # Clear screen
            for key, stim in self.stimuli.iteritems():
                stim.setAutoDraw(False)

        # Flip the screen
        self.fpsCounter.flip()

        # Make Movie
        if self.triggers['startTrigger'] and self.trial.settings['setup']['movie']:
            self.movie.run()
