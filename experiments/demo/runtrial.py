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
import time
import numpy as np
import pygame

# EasyExp modules
from core.Core import Core
from core.BaseTrial import BaseTrial
from core.events.timer import Timer

# Custom imports
#################################
# ADD YOUR CUSTOM IMPORTS BELOW #
#################################
from core.misc.conversion import pol2cart, mm2pix, deg2m


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
    - RunTrial.init_stimuli(): Initialization/Preparation of stimuli. Creation of stimuli objects should be implemented
    here.
    - RunTrial.init_audio(): Initialization/Preparation of auditory stimuli and beeps. Creation of auditory objects
    should be implemented here.
    - RunTrial.get_response(): Participant's response should be handled here. This method is typically called during the
    "response" state.
    - RunTrial.fast_state_machine(): Real-time state machine.
    - RunTrial.graphics_state_machine(): Slow state machine.

    State transition:
    State transition is handled by BaseTrial abstract class. State transition is usually triggered by timers' timeout
     or by key presses as defined in parameters.json file (see documentation for more details). However, transition to
      next state can be forced without waiting by calling self.jump().
    """

    homeMsg = 'Welcome!'  # Message prompted at the beginning of the experiment
    version = '1.0.0'

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
        # Display options
        # if set to False, then display will not be automatically cleared at the end of each trial. This allows
        # continuous rendering with no blank between trials.
        self.clearAll = True

        # Experiment settings
        # ===================
        # Experiment's parameters can accessed by calling self.parameters['parameter_name']
        # Because parameters are loaded from a JSON file, they are imported as string. Therefore, it might be necessary
        # to convert the parameter's type: e.g. as a float number.
        # Example:
        # self.storage['my_parameter'] = float(self.parameters['my_parameter'])

        # Sled settings
        self.storage['pViewer'] = [0.0, 0.0]
        self.storage['mvtBackDuration'] = float(self.parameters['mvtBackDuration'])  # Returning movement duration (in s)
        self.storage['sledHome'] = 0.0  # Sled home position
        self.storage['sledStart'] = float(self.parameters['sledStart'])  # Sled starting position
        self.storage['mvtAmplitude'] = float(self.parameters['movDistance'])  # Movement amplitude
        self.storage['mvtDuration'] = float(self.parameters['movDuration'])  # Movement duration (in s)
        self.storage['sledFinal'] = 0.0  # Sled final position (trial parameter)

        # Feedback message
        self.storage['Feedback_msg_color'] = self.parameters['Feedback_msg_color_default']
        self.storage['Feedback_msg'] = 'Too late'

        # Events triggers
        # ===============
        # Default triggers are moveOnRequested, pauseRequested, startTrigger and quitRequested.
        # They should not be modified. However, you can add new triggers: 'trigger_name': False
        # self.triggers.update({
        #   'trigger_name': False
        # })
        self.triggers.update({
            'calibration_requested': False,
            'feedback': False
        })

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
        #
        # Add your timers to this dictionary.
        # self.timers.update({
        #    'timer_name': Timer()
        # })
        self.timers.update({
            'sled_start': Timer(),
            'responseDuration': Timer()
        })

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
        # =====================
        # self.buttons.add_listener('device_type', 'key_label', key_code)
        # Arguments are: device_type, key label, key code (Pygame constant)
        #
        # For example:
        #
        # self.buttons.add_listener('keyboard', 'a', pygame.K_a)  # key "A"
        # self.buttons.add_listener('mouse', 'left', 0)  # Left mouse click
        # self.buttons.add_listener('mouse', 'right', 2)  # Right mouse click
        self.buttons.add_listener('mouse', 'left', 0)
        self.buttons.add_listener('mouse', 'right', 2)
        self.buttons.add_listener('keyboard', 'calibration', pygame.K_c)

    ################################
    # CUSTOMIZATION STARTS HERE    #
    ################################

    def init_devices(self):
        """
        Setup devices
        Devices must be defined in experiment_folder/devices.json
        Structure of devices.json:
            "devices": {
                "class_name": {
                    "options": {
                        "argument1": value,
                        "argument2": value
                    }
                ]
            }

        "class_name" must match the actual class name of the device (case-sensitive)
        Arguments defined in "options" are those passed to the device class constructor. See the documentation of each
        device (in core/apparatus/device_name/device_name.py) to get the full list of arguments. Note that it is not
        necessary to define all the arguments. Missing arguments will be automatically replaced by class's default
         values.

        For example:
            "devices": {
                "OptoTrak":
                    "options": {
                        "freq": 60.0,
                        "velocity_threshold": 0.01
                    },
                "Sled": {
                    "options": {
                        "server": "sled"
                    }
                }
            }


        RunTrial calls some devices methods automatically if the device's class has such methods:
        - Device::close(): this method should implement the closing method of the device. If does not take arguments.
        - Devices::start_trial(trial_id, trial_parameters): routine called at the beginning of a trial. Parameters are:
            int trial_id: trial number (or unique id)
            dict trial_parameters: Trial.params
        - Devices::stop_trial(trial_id, valid_trial): routine called at the end of a trial. Parameters should be:
            int trial_id: trial number (or unique id)
            bool valid_trial: is it a valid trial or not (e.g.: should it be excluded from analysis).

        Devices are stored in the container self.devices, which acts like a dictionary. To access a device's method:
                self.devices['device_name'].method_name(*args)
        """
        # Do not modify this line
        super(RunTrial, self).init_devices()

        # Customization goes below
        if self.devices['eyetracker'] is not None:
            self.next_state = 'calibration'

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
        Prepare/Make stimuli (Only called once at the beginning of the experiment is self.clearAll if False, or at the 
        beginning of every trial if self.clearAll is True. To update stimuli properties on every trial, refer to 
        RunTrial.update_stimuli()

        Stimuli objects (Psychopy) should be stored in self.stimuli container, for example:
        self.stimuli.add(
            'stimulus_name',
            visual.Circle(self.ptw, radius=2, pos=(0, 0))
        )

        IMPORTANT: stimuli are rendered in the same order as they were added.

        # Stimulus rendering
        # ==================
        Then on every loop, the graphics state machine will automatically call self.stimuli['stimulus_name'].draw() if
        self.stimuli['stimulus_name'].status is True.

        State of each stimulus can be manipulated by doing:
        self.stimuli['stimulus_name'].on() => this will set stimulus' status to True
        or
        self.stimuli['stimulus_name'].off() => this will set stimulus' status to False

        # Accessing/Setting stimulus attributes
        # =====================================
        Stimulus's attribute can be accessed or modified as follows:
        self.stimuli['stimulus_name'].__attribute_name = value
            Example:
                # Set new orientation of stimulus (Psychopy)
                self.stimuli['stimulus_name'].ori = 30
        """
        # Probe size
        probeSizeM = deg2m(float(self.parameters['probeSize']), self.screen.distance/1000.0)*1000.0
        probeSize = 0.5 * mm2pix(probeSizeM, probeSizeM, self.screen.resolution, self.screen.size)  # Radius in pixels

        # Top probe location
        probe1PosM = deg2m(float(self.data['intensity']), self.screen.distance/1000.0)*1000.0
        probeTopPos = mm2pix(probe1PosM, float(self.parameters['probeTop']), self.screen.resolution,
                             self.screen.size)

        # bottom probe location
        probeBottomPos = mm2pix(-probe1PosM, float(self.parameters['probeBottom']), self.screen.resolution,
                                self.screen.size)

        # Fixation point
        fixationSizeM = deg2m(float(self.parameters['fixationSize']), self.screen.distance/1000.0)*1000.0
        fixation = 0.5 * mm2pix(fixationSizeM, fixationSizeM, self.screen.resolution, self.screen.size)

        fillColor = (-0.7, -0.7, -0.7)  # Probe fill color: Mid gray
        lineColor = (-0.7, -0.7, -0.7)  # Probe line color: Mid gray

        # Make stimuli
        if self.trial.parameters['first'] == 'top':
            self.data['probe1'] = probe1PosM  # Save probe coordinates in mm
            self.data['probe2'] = -probe1PosM  # Save probe coordinates in mm
            probe1Pos = probeTopPos
            probe2Pos = probeBottomPos
        else:
            self.data['probe1'] = -probe1PosM  # Save probe coordinates in mm
            self.data['probe2'] = probe1PosM  # Save probe coordinates in mm
            probe1Pos = probeBottomPos
            probe2Pos = probeTopPos

        self.stimuli.add(
            'probe1',
            visual.Circle(self.ptw, radius=probeSize[0], pos=probe1Pos, lineWidth=1, lineColor=lineColor,
                          fillColor=fillColor, units='pix')
        )

        self.stimuli.add(
            'probe2',
            visual.Circle(self.ptw, radius=probeSize[0], pos=probe2Pos, lineWidth=1, lineColor=lineColor,
                          fillColor=fillColor, units='pix')
        )

        self.stimuli.add(
            'fixation',
            visual.Circle(self.ptw, radius=fixation[0], pos=(0.0, 0.0), lineWidth=1, lineColor=(-0.7, -0.7, -0.7),
                          fillColor=(-0.7, -0.7, -0.7), units='pix')
                         )

        self.stimuli.add(
            'feedback',
            visual.TextStim(self.ptw, pos=(0, 0), text=self.storage['Feedback_msg'], units="pix", height=40.0,
                            color=self.storage['Feedback_msg_color'])
        )

    def update_stimuli(self):
        """
        Update stimuli attributes based on trial parameters

        This method is intended to update stimuli already created in BaseTrial.init_stimuli()
        :return: void
        """
        # Top probe location
        probe1PosM = deg2m(float(self.data['intensity']), self.screen.distance / 1000.0) * 1000.0
        probeTopPos = mm2pix(probe1PosM, float(self.parameters['probeTop']), self.screen.resolution,
                             self.screen.size)

        # bottom probe location
        probeBottomPos = mm2pix(-probe1PosM, float(self.parameters['probeBottom']), self.screen.resolution,
                                self.screen.size)

        # Make stimuli
        if self.trial.parameters['first'] == 'top':
            self.data['probe1'] = probe1PosM  # Save probe coordinates in mm
            self.data['probe2'] = -probe1PosM  # Save probe coordinates in mm
            probe1Pos = probeTopPos
            probe2Pos = probeBottomPos
        else:
            self.data['probe1'] = -probe1PosM  # Save probe coordinates in mm
            self.data['probe2'] = probe1PosM  # Save probe coordinates in mm
            probe1Pos = probeBottomPos
            probe2Pos = probeTopPos

        # Update stimuli position based on trial parameters
        self.stimuli['probe1'].setPos(probe1Pos)
        self.stimuli['probe2'].setPos(probe2Pos)

        # Self motion settings
        self.storage['side'] = 1 if self.trial.parameters['side'] == 'right' else -1
        self.storage['sledStart'] = self.storage['side'] * float(self.parameters['sledStart'])
        self.storage['sledFinal'] = self.storage['sledStart'] + self.storage['side'] * self.storage['mvtAmplitude']

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

    # =========================================
    # Eye-tracker related methods
    # =========================================
    def check_calibration_request(self):
        """
        Check if eye-tracker calibration is requested
        :return:
        """
        if self.state != 'calibration' \
                and (self.buttons.get_status('calibration') or self.triggers['calibration_requested']):
            self.triggers['calibration_requested'] = False
            self.next_state = 'calibration'
            self.jump()

    def update_fixation(self):
        """
        Update fixation point position
        :return:
        """
        fixation_position = mm2pix(1000 * self.storage['pViewer'][0], float(self.parameters['fixation_y']),
                                   self.screen.resolution, self.screen.size)
        self.stimuli['fixation'].setPos(fixation_position)  # Update fixation position

    def calibrate_el(self):
        """
        Calibrate Eye-tracker
        :return: void
        """
        with self.lock:
            self.devices['eyetracker'].calibrate(self.ptw,
                                                 custom={
                                                     'radius': 0.5,
                                                     'n': 5,
                                                     'shape': 'rect',
                                                     'ctype': 'HV5'
                                                 },
                                                 drift={
                                                     'x': int(0.5 * self.screen.resolution[0]),
                                                     'y': int(0.5 * self.screen.resolution[1])
                                                 })

    def record_stimuli(self):
        """
        Record stimuli position in eye-tracker data file
        :return: 
        """
        if self.devices['eyetracker'] is not None:
            # Get all stimuli position
            positions = self.stimuli.get_positions()
            positions['sled'] = self.storage['pViewer']
            self.devices['eyetracker'].record(stimuli=positions)

    # =========================================
    # Sled related methods
    # =========================================
    def getviewerposition(self):
        """
        Get viewer (sled) position
        """
        p = self.devices['sled'].getposition(t=self.devices['sled'].client.time())
        self.storage['pViewer'] = (p[0], p[1])

    def wait_sled(self, position):
        """
        Check if sled is at excepted position. If not, then move sled to this position.
        :param position: expected position of sled
        :return: Sled at position and not moving
        """
        return self.devices['sled'].wait_ready(position, duration=self.storage['mvtBackDuration'])

    # =========================================
    # State machines
    # =========================================
    def fast_state_machine(self):
        """
        Real-time state machine: state changes are triggered by keys or timers. States always have the same order.
        This state machine runs at close to real-time speed. Event handlers (key press, etc.) and position trackers
        (optotrak, eye-tracker or sled) should be called within this state machine.
        Rendering of stimuli should be implemented in the graphics_state_machine()
        Default state order is:
        1. loading: preparing experiment (loading devices, ...)
        2. idle: display welcome message and wait for user input
        3. iti: inter-trial interval
        4. init: load trial parameters
        5. start: from here start the custom part. This state must be implemented in RunTrial.fast_state_machine()
        ...
        last. end: end trial and save data

        'loading', 'idle', 'init' and 'end' states are already implemented in BaseTrial.__default_fast_states() method,
        but these implementations can be overwritten in RunTrial.fast_state_machines(). To do so, simply define these
        states as usual. For instance:
        if self.state == "idle":
            # do something
            
        State Transition:
        Transition to next occurs when the current state duration has reached its maximum defined in parameters.json. If
        the state's maximum duration is set to False, then transition must be triggered manually (either by key press or
        by any other custom events). Manual transition can be done by calling RunTrial.jump(). RunTrial.jump() method 
        can also be called for moving to the next state without waiting for the current state to reach its maximum 
        duration.
        """

        if self._running and self.triggers['startTrigger']:
            # Call devices-related methods only if experiment is initialized and running

            # Get sled position
            self.getviewerposition()

            # Record stimuli position in eye-tracker data file
            self.record_stimuli()

            # Check for calibration request
            self.check_calibration_request()

        if self.state == 'pause':
            # PAUSE experiment
            if self.singleshot('pause_sled'):
                # Move the sled back to its default position
                if 'sled' in self.devices and self.devices['sled'] is not None:
                    self.devices['sled'].move(self.storage['sledHome'], self.storage['mvtBackDuration'])
                    time.sleep(self.storage['mvtBackDuration'])
                    self.devices['sled'].lights(True)  # Turn the lights off

        elif self.state == 'calibration':
            # Eye-tracker calibration
            self.next_state = 'iti'
            self.triggers['calibration_requested'] = False

        elif self.state == 'iti':
            if self.singleshot('sled_light'):
                if 'sled' in self.devices:
                    self.devices['sled'].lights(False)  # Turn the lights off

        elif self.state == 'start':
            # Start trial: get trial information and update trial's parameters accordingly
            self.next_state = 'first'

            if self.singleshot('start_trial'):
                # ADD YOUR CODE HERE
                # Stimuli Triggers
                self.triggers['startTrigger'] = True
                self.stimuli['fixation'].on()

                # Compute states duration
                screen_latency = 0.050  # Screen latency in ms
                timings = dict()
                timings['first'] = float(self.trial.parameters['timing']) - screen_latency
                timings['probe1'] = float(self.parameters['probeDuration'])
                timings['probeInterval'] = float(self.parameters['probeInterval'])
                timings['probe2'] = timings['probe1']
                timings['last'] = 0.0

                # Update states duration
                self.durations = timings

            # Move sled to starting position if it is not there already
            if self.wait_sled(self.storage['sledStart']):
                self.jump()

        elif self.state == 'first':
            self.next_state = 'probe1'
            if self.singleshot('sled_start'):
                self.timers['sled_start'].start()
                self.devices['sled'].move(self.storage['sledFinal'], self.storage['mvtDuration'])

        elif self.state == 'probe1':
            self.next_state = 'probeInterval'
            self.stimuli['probe1'].on()
            if self.singleshot():
                self.data['sled_probe1'] = self.storage['pViewer'][0]
                self.data['time_probe1'] = self.timers['sled_start'].get_time('elapsed')

        elif self.state == 'probeInterval':
            self.next_state = 'probe2'
            self.stimuli['probe1'].off()

        elif self.state == 'probe2':
            self.next_state = 'last'
            self.stimuli['probe2'].on()
            if self.singleshot():
                self.data['sled_probe2'] = self.storage['pViewer'][0]
                self.data['time_probe2'] = self.timers['sled_start'].get_time('elapsed')

        elif self.state == 'last':
            self.next_state = 'response'
            self.stimuli['probe2'].off()

        elif self.state == 'response':
            self.next_state = 'feedback'

            # Get participant's response
            self.get_response()

        elif self.state == 'feedback':
            self.next_state = "end"

            if self.singleshot('feedback'):
                self.validTrial = self.triggers['response_given']  # Is the current trial valid

                # By default, no feedback
                self.triggers['feedback'] = False

                if not self.validTrial:
                    self.triggers['feedback'] = True
                    self.storage['Feedback_msg'] = 'Too late'
                    self.sounds['wrong'].play()

                # Move directly to end state if no feedback
                if self.validTrial:
                    self.jump()

    def graphics_state_machine(self):
        """
        Graphical (slow) state machine: running speed of this state machine is limited by the screen's refresh rate. For
        instance, this state machine will be updated every 17 ms with a 60Hz screen. For this reason, only slow events
        (display of stimuli) should be described here. Everything that requires faster (close to real-time) processing
        should be specified in the RunTrial::fast_state_machine() method.
        Default state order is:
        1. loading: preparing experiment (loading devices, ...)
        2. idle: display welcome message and wait for user input
        3. iti: inter-trial interval
        4. init: load trial parameters
        5. start: from here start the custom part. This state must be implemented in RunTrial.fast_state_machine()
        ...
        last. end: end trial and save data

         'loading', 'idle', and 'pause' states are already implemented in BaseTrial.__default_fast_states() method, but
        these implementations can be overwritten in RunTrial.fast_state_machines(). To do so, simply define these states
        as usual. For instance:
        if self.state == "idle":
            # do something
        """
        if self.state == 'calibration':
            if self.singleshot('el_calibration'):
                self.calibrate_el()
            self.default_stimuli['continue'].draw()

        elif self.state == 'feedback':
            if self.singleshot('feedback_clear'):
                self.clear_screen()

            if self.triggers['feedback']:
                if self.singleshot('feedback_create'):
                    # For some reasons, text stimuli properties cannot be updated, so we need to create a new one
                    self.stimuli.add(
                        'feedback',
                        visual.TextStim(self.ptw, pos=(0, 0), text=self.storage['Feedback_msg'], units="pix",
                                        height=40.0, color=self.storage['Feedback_msg_color'])
                    )
                self.stimuli['feedback'].draw()

        # Update fixation position (body-fixed)
        if self.triggers['startTrigger']:
            # Update fixation position
            self.update_fixation()

