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
        # Display options
        # if set to False, then display will not be automatically cleared at the end of each trial. This allows
        # continuous rendering with no blank between trials.
        self.clearAll = True

        # Experiment settings
        # ===================
        # Experiment's parameters can accessed by calling self.trial.parameters['parameter_name']
        # Because parameters are loaded from a JSON file, they are imported as string. Therefore, it might be necessary
        # to convert the parameter's type: e.g. as a float number.
        # Example:
        # self.my_parameter = float(self.trial.parameters['my_parameter']

        # Events triggers
        # ===============
        # Default triggers are moveOnRequested, pauseRequested, startTrigger and quitRequested.
        # They should not be modified. However, you can add new triggers: 'trigger_name': False
        # self.triggers.update({
        #   'trigger_name': False
        # })

        # Stimulus triggers
        #
        # Stimuli triggers can be added by calling:
        # self.stimuliTrigger.add('stimulus_name', 'value')
        # If value is not provided, then False will be set by default.
        #
        # IMPORTANT: if 'stimulus_name' is added to self.stimuliTrigger, then it should also be added to self.stimuli
        # dictionary in RunTrial.init_stimuli() method
        #
        # stimuliTrigger acts like a dictionary. item's value can be accessed by calling:
        # self.stimuliTrigger['stimulus_name']
        #
        # and new trigger value can be set by calling:
        # self.stimuliTrigger['stimulus_name'] = True
        #
        # if self.stimuliTrigger['stimulus_name'] is True, then self.stimuli['stimulus_name'].draw() will be called.
        #
        # IMPORTANT: stimuli are rendered in the same order as the triggers defined in stimuliTrigger dictionary.
        self.stimuliTrigger.add('my_circle')

        # Timers
        # ======
        # Timers act like a watch.
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

        # Data
        # ====
        # Data field that will be output into the data file should be specified here.
        self.data = {
            'field_name': None
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
        """

        # Get sled (viewer) position
        if self._running:
            # Here you can call devices methods. Devices' methods can't be called before self._running is True.
            pass

        if self.state == 'start':
            # The START state is dedicated to initialization of parameters/variables used in the current trial.
            # Trial parameters can be accessed by calling: self.trial.params['parameter_name']
            # It custom variables needs to be accessed outside this state, then it is recommended to bind them to the
            # current RunTrial instance. For example:
            # self.my_new_variable = something
            # IMPORTANT: in this case, self.my_new_variable should initialized in RunTrial's constructor. For example:
            # self.my_new_variable = None

            self.next_state = 'draw_circle'

            if self.singleshot('start_trial'):
                # This is a singleshot event: instructions within this block will be executed only once.
                # You can define as many singleshot events as you need during a state as long as you provide a different
                # label every time.
                # For example:
                #   self.singleshot('event_1') => will be triggered only once
                #   self.singleshot('event_2') => will be triggered only once
                #   self.singleshot('event_2') => will NOT be triggered because this label has been already used.
                #
                # You can also bind a function to a singleshot event:
                #   self.singleshot.run('event', target=function_name, **function_arguments)
                #
                #  For example:
                #   # A simple function that print some text
                #   def show_text(text):
                #       print(text)
                #
                #   # This will call show_text() function only once
                #   self.singleshot.run('name_of_event', target=show_text, text='Hello, world!')

                # ADD YOUR CODE HERE
                # Stimuli Triggers
                self.triggers['startTrigger'] = True  # If not set to True, then stimuli will not be rendered

                # Modifying states duration dynamically if needed
                # 1) Add new durations
                timings = {
                    'name_of_state': 0.5
                }
                # 2) Update states durations
                self.durations = timings

        elif self.state == 'draw_circle':
            self.next_state = 'response'
            # Set trigger to True (from here, the corresponding stimulus will be drawn until told otherwise)
            self.stimuliTrigger['my_circle'] = True

        elif self.state == 'response':
            self.next_state = 'end'

            # Get participant's response
            self.get_response()
            if self.triggers['response_given']:
                # If response is given, then we move directly to the next state ('end') without waiting for the end of
                #  the response phase
                self.change_state(force_move_on=True)

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
        if self.state == 'draw_cicle':
            # Example: make the circle jumping to a next random location
            current_position = self.stimuli['my_circle'].pos
            max_amplitude = 50  # jump size
            new_position = current_position + np.random.uniform(-1, 1) * max_amplitude
            self.stimuli['my_circle'].setPos(new_position)  # Update fixation position

