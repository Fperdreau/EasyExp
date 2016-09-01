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

# Psychopy
# Use pyo library instead of Pygame
from psychopy import prefs
prefs.general['audioLib'] = ['pygame']
from psychopy import visual, sound
import pygame
import time
import numpy as np

# EasyExp modules
from core.Core import Core
from core.BaseTrial import BaseTrial
from core.buttons.buttons import UserInput
from core.events.timer import Timer

# Custom imports
#################################
# ADD YOUR CUSTOM IMPORTS BELOW #
#################################
from core.misc.conversion import pol2cart, mm2pix, deg2m
from core.apparatus.sled.sled import Sled
from core.apparatus.optotrak.optotrak import OptoTrak
from core.apparatus.eyetracker.eyetracker import EyeTracker


class RunTrial(BaseTrial):
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
        # DO NOT MODIFY
        super(RunTrial, self).__init__(exp_core=exp_core)

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
            'stimulus_name': False,
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
            'timer_name': Timer()
        }

        # Data
        # ====
        # Data field that will be output into the data file should be specified here.
        self.data = {
            'field_name': None
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
        # Example 1: Create Sled instance
        self.devices['sled'] = Sled(dummy_mode=not self.trial.settings['devices']['sled'], server='sled')

        # Example 2: Create eye-tracker instance
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

        # Example 3: Create OptoTrak instance
        user_file = '{}_{}_{}.txt'.format(self.user.dftName, 'optotrak', time.strftime('%d-%m-%Y_%H%M%S'))
        self.devices['optotrak'] = OptoTrak(user_file=user_file, freq=200.0, velocity_threshold=0.1,
                                            time_threshold=100, origin='origin',
                                            labels=('Xas', 'Marker2', 'Yas', 'origin', 'hand1', 'hand2'),
                                            dummy_mode=not self.trial.settings['devices']['optotrak'],
                                            tracked={'Xas', 'Marker2', 'Yas', 'origin', 'hand1', 'hand2'})
        self.devices['optotrak'].init()

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
        self.stimuli['my_circle'] = visual.Circle(self.ptw, radius=30, pos=(0, 0), lineWidth=1,
                                                  lineColor=(0.0, 0.0, 0.0), fillColor=(0.0, 0.0, 0.0), units='pix')

    def get_response(self):
        """
        Get participant' response
        """
        # Initialize response timer
        if self.timers['responseDuration'] is None or self.timers['responseDuration'].get_time('start') is None:
            self.timers['responseDuration'] = Timer()
            self.timers['responseDuration'].start()

        # Get some response (e.g. check buttons status)
        response_received = self.buttons.get_status('left') or self.buttons.get_status('right')

        # if response has been given for the first time, then process it
        if not self.triggers['response_given'] and response_received:
            self.triggers['response_given'] = True  # Yes, we got a response

            # Stop response timer, store response duration, and reset timer
            self.timers['responseDuration'].stop()
            self.data['responseDuration'] = round(self.timers['responseDuration'].get_time('elapsed')*1000.0)
            self.timers['responseDuration'].reset()

            # Do something with the response: for instance, is it a correct answer?
            self.data['response'] = 'left' if self.buttons.get_status('left') else 'right'
            self.data['correct'] = self.data['response'] == 'right'

    # =========================================
    # State machines
    # =========================================
    def fast_state_machine(self):
        """
        Real-time state machine: state changes are triggered by keys or timers. States always have the same order.
        This state machine runs at close to real-time speed. Event handlers (key press, etc.) and position trackers
        (optotrak, eye-tracker or sled) should be called within this state machine.
        Rendering of stimuli should be implemented in the graphics_state_machine()
        """

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
            self.nextState = 'response'

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
                # Stimuli Triggers
                self.triggers['startTrigger'] = True  # Draw stimuli

        elif self.state == 'response':
            self.nextState = 'end'

            # Get participant's response
            self.get_response()

            # If we got a response, then move to next state
            if self.triggers['response_given']:
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