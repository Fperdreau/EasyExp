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
import numpy as np

# EasyExp modules
from core.Core import Core
from core.BaseTrial_threaded import BaseTrialThreaded


# Custom imports
#################################
# ADD YOUR CUSTOM IMPORTS BELOW #
#################################


class RunTrial(BaseTrialThreaded):
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

        # Events triggers
        # ===============
        # Default triggers are moveOnRequested, pauseRequested, startTrigger and quitRequested.
        # They should not be modified. However, you can add new triggers: 'trigger_name': False
        # self.triggers.update({
        #   'trigger_name': False
        # })

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
        self.stimuli.add(
            'my_circle',
            visual.Circle(self.ptw, radius=30, pos=(0, 0), lineWidth=1, lineColor=(0.0, 0.0, 0.0),
                          fillColor=(0.0, 0.0, 0.0), units='pix')
        )

    def update_stimuli(self):
        """
        Update stimuli attributes based on trial parameters

        This method is intended to update stimuli already created in BaseTrial.init_stimuli()
        :return: void
        """

    def get_response(self):
        """
        Get participant' response
        """
        pass

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

        # Get sled (viewer) position
        if self._running:
            # Here you can call devices methods. Devices' methods can't be called before self._running is True.
            pass

        if self.state == 'start':
            # The START state is dedicated to initialization of parameters/variables used in the current trial.
            # Trial parameters can be accessed by calling: self.trial.parameters['parameter_name']
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
            self.next_state = 'jump_circle'
            # Set trigger to True (from here, the corresponding stimulus will be drawn until told otherwise)
            self.stimuli['my_circle'].on()

        elif self.state == 'jump_circle':
            self.next_state = 'hide_circle'

        elif self.state == 'hide_circle':
            self.next_state = 'response'
            # Prevent stimulus from being drawn
            self.stimuli['my_circle'].off()

        elif self.state == 'response':
            self.next_state = 'end'

            # Get participant's response
            self.get_response()
            if self.triggers['response_given']:
                # If response is given, then we move directly to the next state ('end') without waiting for the end of
                #  the response phase
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
        if self.state == 'jump_circle':
            if self.singleshot('jump_circle'):
                # Example: make the circle jumping to a next random location
                current_position = self.stimuli['my_circle'].pos
                max_amplitude = 50  # jump size
                new_position = current_position + np.random.uniform(-1, 1) * max_amplitude
                self.stimuli['my_circle'].setPos(new_position)  # Update stimulus position

