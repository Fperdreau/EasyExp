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
from psychopy import visual
from psychopy import sound
import pygame
import time
import numpy as np

# Multi-threading
import threading

# Loger
import logging

# EasyExp modules
from Core import Core
from movie.moviemaker import MovieMaker
from buttons.buttons import UserInput
from events.timer import Timer
from StateMachine import StateMachine
from stimuli.stimuli import Stimuli

# Define globals
Lock = threading.RLock()


class Loading(object):
    """
    A simple loading animation
    """
    __dft_text = 'Loading '
    __animation_style = '.'
    __animation = ''
    __msg = ''
    __n = 0
    __dt = 0.500
    __timer = Timer()

    @property
    def text(self):
        """
        :rtype: str
        :return:
        """
        if self.__timer.get_time('start') is None:
            self.__timer.start()

        if self.__n == 0:
            self.__animation = ''

        if self.__timer.get_time('elapsed') >= self.__dt:
            self.__animation = '{}{}'.format(self.__animation, self.__animation_style)
            self.__n += 1
            if self.__n > 3:
                self.__n = 0

            # Reset timer
            self.__timer.reset()

        # Update message
        self.__msg = "{}{}".format(self.__dft_text, self.__animation)
        return self.__msg


class TimeUp(object):
    """
    A simple Timeup animation
    """

    def __init__(self, max_duration):
        self.__max_duration = max_duration
        self.__timer = Timer(max_duration=max_duration)

    @property
    def text(self):
        """
        :rtype: str
        :return:
        """
        if self.__timer.get_time('start') is None:
            self.__timer.start()
        return "Experiment will continue in {0:1.1f} s".format(self.__timer.countdown)


class BaseTrial(StateMachine):
    """
    BaseTrial class
    Abstract class handling trial's procedure

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
    - BaseTrial.__init__(): Class's constructor. Initialize triggers, inputs, devices, etc.
    - BaseTrial.init_devices(): devices used in the experiment and defined in devices.json are initialized here.
    - BaseTrial.init_trial(): Initialization of trial (get trial's information, reset triggers and data). This method
    should not be modified
    - BaseTrial.init_stimuli(): Must be implemented by RunTrial.
    - BaseTrial.init_audio(): Must be implemented by RunTrial.
    - BaseTrial.quit(): Quit experiment. This method is called when the experiment is over (no more trials to be played)
    or when the user press the "quit" key.
    - BaseTrial.go_next(): Check if transition to next state is requested (by key press or timer)
    - BaseTrial.get_response(): Must be implemented by RunTrial.
    - BaseTrial.end_trial(): End trial routine. Write data into file and check if the trial is valid or invalid.
    - BaseTrial.run(): Application's main loop.
    - BaseTrial.change_state(): handles transition between states.
    - BaseTrial.fast_state_machine(): Real-time state machine.
    - BaseTrial.graphics_state_machine(): Slow state machine.
    - BaseTrial.__default_fast_states(): Definition of default state for fast_state_machine
    - BaseTrial.__default_graphic_states(): Definition of default state for graphics_state_machine
    - BaseTrial.update_graphics(): Render stimuli. More specifically, it check status of stimuli triggers and it a 
    trigger is True, then it renders the corresponding stimulus stored in self.stimuli dictionary.
    """

    __homeMsg = 'Welcome!'  # Message prompted at the beginning of the experiment
    __loading = Loading()
    __countdown = None

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
        super(BaseTrial, self).__init__()

        self.core = exp_core  # EasyExp Core instance
        self.screen = exp_core.screen  # Screen instance
        self.trial = exp_core.trial  # Trial instance
        self.user = exp_core.user  # User instance
        self.parameters = exp_core.parameters  # Experiment parameters
        self.ptw = self.screen.ptw  # Window pointer
        self.logger = exp_core.logger  # EasyExp logger
        self.textToDraw = BaseTrial.__homeMsg  # Default welcome message

        self.status = True  # Experiment status (True=running)
        self._running = False  # First Experiment initialization completed
        self._initialized = False  # First trial initialization completed
        self.validTrial = True  # Trial validity
        self.threads = dict()  # Thread container
        self.lock = Lock  # Thread Lock
        self.add_syncer(2, self.lock)  # Add sync manager

        # State Machine
        # =============
        # Default states duration
        self.durations = {
            'loading': 0.0,
            "quit": 0.0,
            "idle": False,
            "pause": self.trial.pause_duration,
            "init": 0.0,
            "end": 0.0
        }
        # Custom states duration specified in parameters.json
        self.durations.update(self.parameters['durations'])

        self.state = 'loading'
        self.next_state = 'idle'

        # Display options
        # if set to False, then display will not be automatically cleared at the end of each trial. This allows
        # continuous rendering with no blank between trials.
        self.clearAll = True

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

        # Stimuli
        # =======
        # Stimulus container

        # See BaseTrial.init_stimuli() for documentation about how to add stimuli
        self.stimuli = Stimuli()

        # Default stimuli
        self.default_stimuli = Stimuli()
        self.__init_default_stimuli()

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
            'loading': Timer()
        }

        # Data
        # ====
        # Data field that will be output into the data file should be specified here.
        self.data = dict()

        # Storage
        # =======
        # Any customized variable (e.g. not defined in the settings, parameters or conditions file) should be added to
        # this dictionary.
        # e.g. self.storage['my_variable'] = value
        self.storage = dict()

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
        # Inputs.get_status('_name_of_key')  # returns True or False
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

        # Devices
        # Devices should be implemented in RunTrial::init_devices() method.
        # =======
        self.devices = exp_core.devices

        # Audio/Video
        # ===========
        # Initialize audio
        self.sounds = dict()
        self.movie = None

    # =========================================
    # STATE MACHINE
    # =========================================
    def run(self):
        """
        Application main loop
        DO NOT MODIFY
        """
        self.threads['fast'] = threading.Thread(target=self.fast_loop, name='fast')
        self.threads['fast'].daemon = False
        self.threads['fast'].start()
        self.graphics_loop()
        self.quit()

    def graphics_loop(self):
        """
        Graphic state machine loop
        :return:
        """
        counter = 0
        init_time = time.time()
        while self.status:
            # Default states for this state machine
            self.__default_graphic_states()

            # Custom Graphics state
            self.graphics_state_machine()

            # Add state to watcher
            self._syncer.count('graphics', self.state)

            # Update display
            self.update_graphics()

            # Increment loop counter
            counter += 1

        # Compute average looping time
        lapses = (time.time() - init_time) / float(counter)
        self.logger.debug('Average lapse for GRAPHICS: {} ms'.format(lapses * 1000))

    def fast_loop(self):
        """
        Fast state machine loop
        :return:
        """
        counter = 0
        init_time = time.time()
        while self.status:

            if self._running:
                # Update input devices state
                self.buttons.update()
                self.go_next()

            # Check state status
            if self.change_state():
                # Send events to devices that will be written into their data file
                for device in self.devices:
                    if hasattr(self.devices[device], 'send_message'):
                        self.devices[device].send_message('EVENT_STATE_{}'.format(self.state))

            # Default states for this state machine
            self.__default_fast_states()

            # Custom Fast states
            self.fast_state_machine()

            # Add state to watcher
            self._syncer.count('fast', self.state)

            # Increment loop counter
            counter += 1

        # Compute average looping time
        lapses = (time.time() - init_time) / float(counter)
        self.logger.debug('Average lapse for FAST: {} ms'.format(lapses * 1000))

    def quit(self):
        """
        Quit experiment
        :return:
        """
        # Set in idle mode
        self.state = 'idle'
        self.textToDraw = "Experiment is over!"

        # Shutdown devices
        self.devices.close_all()

        self.status = False

        # Quit all opened threads
        for t in self.threads:
            if self.threads[t].isAlive():
                self.threads[t].join()

    def go_next(self):
        """
        Check if it is time to move on to the next state. State changes can be triggered by key press (e.g.: ESCAPE key)
        or timers. States' duration can be specified in the my_project_name/experiments/experiment_name/parameters.json
        file.
        :rtype: void
        """
        # Does the user want to quit the experiment?
        if self.buttons.get_status('quit'):
            self.next_state = 'quit'
            self.jump()

        # Does the user want a break?
        if self.buttons.get_status('pause'):
            self.next_state = 'pause'
            self.jump()

        if self.buttons.get_status('move_on'):
            self.request_move_on()

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
            return False
        else:
            self.status = status
            if self.status is "pause":
                return 'pause'

            # Assume trial is valid by default
            self.validTrial = True

            # Start a new trial
            # Reset timers
            for timer, value in self.timers.iteritems():
                self.timers[timer].reset()

            # Reset data
            for data, value in self.data.iteritems():
                self.data[data] = None

            # Reset event triggers
            for label, value in self.triggers.iteritems():
                self.triggers[label] = False

            # Update experiment method
            if hasattr(self.trial, 'method') and self.trial.method is not None and hasattr(self.trial.method, 'update'):
                if 'staircaseID' in self.trial.parameters:
                    intensity = self.trial.method.update(int(self.trial.parameters['staircaseID']),
                                                         int(self.trial.parameters['staircaseDir']))
                    self.data['intensity'] = intensity

            # Send START_TRIAL to devices
            for device in self.devices:
                if hasattr(self.devices[device], 'start_trial'):
                    self.devices[device].start_trial(self.trial.id, self.trial.parameters)

            # Initialize movie if requested
            if self.trial.settings['setup']['movie']:
                self.movie = MovieMaker(self.ptw, "{}_TrialID_{}".format(self.core.expname, self.trial.id), "png")

            # Reset all stimuli triggers
            if not self._initialized or self.clearAll:
                with self.lock:
                    self.stimuli.remove_all()
                    self.init_stimuli()

            # Update stimuli based on trial parameters
            with self.lock:
                self.update_stimuli()

            return True

    def end_trial(self):
        """
        End trial routine
        :return:
        """
        # Did we get a response from the participant?
        self.timers['runtime'].reset()

        # Close movie file is necessary
        if self.trial.settings['setup']['movie']:
            self.movie.close()

        # Replay the trial if the user did not respond fast enough or moved the hand before the response phase
        self.logger.logger.debug('[{}] Trial {} - Results:'.format(__name__, self.trial.id))
        for data, value in self.data.iteritems():
            self.logger.logger.debug('[{}] {}: {}'.format(__name__, data, value))
        self.logger.logger.info('[{}] Trial {} - Valid: {}'.format(__name__, self.trial.id, self.validTrial))

        self.trial.stop(self.validTrial)  # Stop routine
        self.trial.write_data(self.data)  # Write data

        # Call closing trial routine
        for device in self.devices:
            if hasattr(self.devices[device], "stop_trial"):
                self.devices[device].stop_trial(self.trial.id, self.validTrial)

    def update_graphics(self):
        """
        Update graphics
        This function check status of stimuli triggers, and if True, then draw the corresponding stimulus object.
        Stimuli are drawn in the same order as triggers defined in stimuliTrigger dictionary.
        :return:
        """
        # Draw stimuli
        if self._initialized and (self.triggers['startTrigger'] or not self.clearAll):
            for stim, stimulus in self.stimuli.iteritems():
                if stimulus.status:
                    self.stimuli[stim].draw()

        elif self.clearAll:
            # Clear screen
            self.clear_screen()

        # Flip the screen
        self.ptw.flip()

        # Make Movie
        if self.triggers['startTrigger'] and self.trial.settings['setup']['movie']:
            self.movie.run()

    def clear_screen(self):
        """
        Clear screen: set all stimuli triggers to False
        """
        with self.lock:
            # Clear screen
            for key, stimulus in self.stimuli.iteritems():
                self.stimuli[key].setAutoDraw(False)

            # Reset all triggers
            self.stimuli.reset()

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
        # Initialize all devices
        self.devices.init(ptw=self.screen.ptw)

    def init_audio(self):
        """
        Initialize sounds
        Auditory stimuli are created here and should be stored in RunTrial.sounds dictionary. For example:
        self.sounds['stimulus_name'] = sound.SoundPygame(secs=0.1, values=880)

        Then you can play the sound by calling:
        self.sounds['stimulus_name'].play()

        :return:
        """
        raise NotImplementedError('Should implement this')

    def __init_default_stimuli(self):
        """
        Add default stimuli.
        Default stimuli can be customized but they should not be removed.
        :return: void
        """
        # Loading text
        self.default_stimuli.add('loading', visual.TextStim(self.ptw, pos=(0, 0), text="Loading", units="pix",
                                                            height=40.0))

        # Welcome message
        self.default_stimuli.add('welcome', visual.TextStim(self.ptw, pos=(0, 0), text=self.textToDraw, units="pix",
                                                            height=40.0))

        # Exit message
        self.default_stimuli.add('quit', visual.TextStim(self.ptw, pos=(0, 0), text="Experiment is over", units="pix",
                                                         height=40.0))

        # Pause text
        self.default_stimuli.add('pause_txt', visual.TextStim(self.ptw, pos=(0, 0), text="Pause", units="pix",
                                                              height=40.0))

        # Countdown text (displayed during breaks)
        self.default_stimuli.add('countdown', visual.TextStim(self.ptw, pos=(0, -50), text="Countdown", units="pix",
                                                              height=40.0))

        # Continue message
        self.default_stimuli.add('continue', visual.TextStim(self.ptw, pos=(0, -50), text="Click to continue",
                                                             units="pix", height=40.0))

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
        raise NotImplementedError('Should implement this')

    def update_stimuli(self):
        """
        Update stimuli attributes based on trial parameters

        This method is intended to update stimuli already created in BaseTrial.init_stimuli()
        :return: void
        """
        pass

    def get_response(self):
        """
        Get participant' response
        """
        raise NotImplementedError('Should implement this')

    def __default_fast_states(self):
        """
        Define default fast states
        Default flow is:
        loading -> idle -> iti -> init -> ...(custom states)... -> end
        :return:
        """
        if self.state == 'loading':
            self.next_state = 'idle'
            if self.singleshot('loading'):
                self.init_devices()

                self.init_audio()

                self._running = True

        elif self.state == 'idle':
            # IDLE state
            # DO NOT MODIFY
            self.next_state = 'iti'

        elif self.state == 'iti':
            # Inter-trial interval
            self.next_state = 'init'

        elif self.state == 'init':
            # Get trial information and update trial's parameters accordingly
            self.next_state = 'start'

            if self.singleshot('init_trial'):
                status = self.init_trial()  # Get trial parameters
                if not status:
                    self.next_state = 'quit'
                    self.jump()
                if status is 'pause':
                    self.next_state = 'pause'
                    self.jump()

                self._initialized = True

        elif self.state == 'quit':
            # QUIT experiment
            # DO NOT MODIFY
            if self.singleshot():
                self.triggers['quitRequested'] = False
                self.clear_screen()
                self.status = False
                self._running = False

        elif self.state == 'pause':
            # PAUSE experiment
            # DO NOT MODIFY
            self.next_state = 'iti'
            self.triggers['pauseRequested'] = False
            if self.singleshot('run_pause'):
                self.trial.run_pause(force=True)

        elif self.state == 'end':
            # End of trial. Call ending routine.
            if self.triggers['pauseRequested']:
                self.next_state = "pause"
            elif self.triggers['quitRequested']:
                self.next_state = "quit"
            else:
                self.next_state = 'iti'

            if self.singleshot():
                self.triggers['startTrigger'] = False

                # End trial routine
                self.end_trial()

    def __default_graphic_states(self):
        """
        Define default graphics states
        :return:
        """

        if self.state == 'loading':
            """
            Display loading message while preparing the experiment
            """
            self.default_stimuli['loading'].setText(self.__loading.text)
            self.default_stimuli['loading'].draw()

        elif self.state == 'idle':
            self.default_stimuli['welcome'].draw()

        elif self.state == 'quit':
            if self.singleshot('quit_graphics'):
                self.clear_screen()
            self.default_stimuli['quit'].draw()

        elif self.state == 'pause':
            if self.singleshot('pause_graphics'):
                # Clear the screen
                self.clear_screen()

                # Make text stimulus
                self.default_stimuli['pause_txt'].setText('PAUSE {0}/{1} [Replayed: {2}]'.format(self.trial.nplayed,
                                                                                                 self.trial.ntrials,
                                                                                                 self.trial.nreplay))
                # Make countdown stimulus if necessary
                if self.trial.settings['setup']['pauseDur'] > 0:
                    self.__countdown = TimeUp(self.durations['pause'])

            self.default_stimuli['pause_txt'].draw()
            # Show countdown if experiment starts automatically after some delay
            if self.__countdown is not None:
                self.default_stimuli['countdown'].setText(self.__countdown.text)
                self.default_stimuli['countdown'].draw()

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
        raise NotImplementedError('Should implement this')

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
        raise NotImplementedError('Should implement this')


