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
from display.fpscounter import FpsCounter
from events.timer import Timer
from StateMachine import StateMachine
from core.stimuli.trigger import Trigger


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


class BaseTrial(StateMachine):
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

    __homeMsg = 'Welcome!'  # Message prompted at the beginning of the experiment
    __loading = Loading()

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

        self.core = exp_core
        self.screen = exp_core.screen
        self.trial = exp_core.trial
        self.user = exp_core.user
        self.ptw = self.screen.ptw
        self.logger = exp_core.logger
        self.textToDraw = BaseTrial.__homeMsg

        self.status = True
        self._running = False
        self.validTrial = False
        self.threads = dict()
        self.lock = threading.RLock()

        # Dependencies
        # ============
        # FPScounter: measures flip duration or simply flips the screen
        self.fpsCounter = FpsCounter(self.screen.ptw)

        # State Machine
        # =============
        # Default states duration
        self.durations = {
            'loading': 0.0,
            "quit": 0.0,
            "idle": False,
            "pause": False,
            "init": 0.0
        }
        # Custom states duration specified in parameters.json
        self.durations = self.trial.parameters['durations']
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
        self.stimuli = dict()

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
        self.stimuliTrigger = Trigger()

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
        import copy
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
        while self.status:
            # Default states for this state machine
            self.__default_graphic_states()

            # Custom Graphics state
            self.graphics_state_machine()

            # Update display
            self.update_graphics()

    def fast_loop(self):
        """
        Fast state machine loop
        :return:
        """
        while self.status:
            if self._running:
                # Update input devices state
                self.buttons.update()
                move_on = self.go_next()
            else:
                move_on = False

            # Default states for this state machine
            self.__default_fast_states()

            # Check state status
            if self.change_state(force_move_on=move_on):
                # Send events to devices that will be written into their data file
                for device in self.devices:
                    if hasattr(self.devices[device], 'send_message'):
                        self.devices[device].send_message('EVENT_STATE_{}'.format(self.state))

            # Custom Fast states
            self.fast_state_machine()

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

        # Quit all opened threads
        for t in self.threads:
            if self.threads[t].isAlive():
                self.threads[t].join()

    def go_next(self):
        """
        Check if it is time to move on to the next state. State changes can be triggered by key press (e.g.: ESCAPE key)
        or timers. States' duration can be specified in the my_project_name/experiments/experiment_name/parameters.json
        file.
        :rtype: bool
        """
        if self.triggers['moveOnRequested']:
            return True

        # Does the user want to quit the experiment?
        if self.buttons.get_status('quit'):
            self.triggers['quitRequested'] = True
            self.next_state = 'quit'
            return True

        # Does the user want a break?
        if self.buttons.get_status('pause'):
            self.triggers['pauseRequested'] = True
            self.next_state = 'pause'
            return True

        return False

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
            self.next_state = 'quit'
            self.change_state(force_move_on=True)
            return False
        else:
            self.status = status
            if self.status is "pause":
                self.triggers['pauseRequested'] = True
                self.next_state = 'pause'
                self.change_state(force_move_on=True)
                return 'pause'

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
                intensity = self.trial.method.update(int(self.trial.params['staircaseID']),
                                                     int(self.trial.params['staircaseDir']))
                self.logger.info('New stimulus intensity: {}'.format(intensity))
                self.data['intensity'] = intensity

            # Send START_TRIAL to devices
            for device in self.devices:
                if hasattr(self.devices[device], 'start_trial'):
                    self.devices[device].start_trial(self.trial.id, self.trial.params)

            # Initialize movie if requested
            if self.trial.settings['setup']['movie']:
                self.movie = MovieMaker(self.ptw, "{}_TrialID_{}".format(self.core.expname, self.trial.id), "png")

            # Initialize stimuli
            self.init_stimuli()

            # Reset stimuli triggers and make sure that there is a stimulus trigger for every stimulus defined in
            # self.stimuli dictionary.
            for label, obj in self.stimuli.iteritems():
                if label in self.stimuliTrigger:
                    self.stimuliTrigger[label] = False
                else:
                    self.stimuliTrigger.add(label, False)

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

    def update_graphics(self):
        """
        Update graphics
        This function check status of stimuli triggers, and if True, then draw the corresponding stimulus object.
        Stimuli are drawn in the same order as triggers defined in stimuliTrigger dictionary.
        :return:
        """
        # Draw stimuli
        if self.triggers['startTrigger']:
            for stim, status in self.stimuliTrigger.iteritems():
                if stim in self.stimuli:
                    if status:
                        self.stimuli[stim].draw()
                else:
                    msg = Exception(
                        'Stimulus "{}" has not been initialized in RunTrial::init_stimuli() method!'.format(
                            stim))
                    self.logger.logger.critical(msg)
                    raise msg
        elif self.clearAll:
            # Clear screen
            self.clear_screen()

        # Flip the screen
        self.fpsCounter.flip()

        # Make Movie
        if self.triggers['startTrigger'] and self.trial.settings['setup']['movie']:
            self.movie.run()

    def clear_screen(self):
        """
        Clear screen: set all stimuli triggers to False
        """
        # Clear screen
        for key, stim in self.stimuli.iteritems():
            stim.setAutoDraw(False)

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
        raise NotImplementedError('Should implement this')

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

    def init_stimuli(self):
        """
        Prepare/Make stimuli

        Stimuli objects (Psychopy) should be stored in self.stimuli dictionary, for example:
        self.stimuli['stimulus_name'] = visual.Circle(self.ptw, radius=2, pos=(0, 0))

        Then on every loop, the state machine will automatically call self.stimuli['stimulus_name'].draw() if
        self.stimuliTrigger['stimulus_name'] is set to True.
        """
        raise NotImplementedError('Should implement this')

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
        if self.state == 'pause':
            self.next_state = 'iti'

        elif self.state == 'loading':
            self.next_state = 'idle'
            if self.singleshot('loading'):
                self.init_devices()

                self.init_audio()

                self._running = True

        elif self.state == 'idle':
            # IDLE state
            # DO NOT MODIFY
            self.next_state = 'iti'
            if self.buttons.get_status('move_on'):
                self.change_state(True)

        elif self.state == 'iti':
            # Inter-trial interval
            self.next_state = 'init'

        elif self.state == 'init':
            # Get trial information and update trial's parameters accordingly
            self.next_state = 'start'

            if self.singleshot():
                status = self.init_trial()  # Get trial parameters
                if not status:
                    self.next_state = 'quit'
                    self.change_state(force_move_on=True)
                if status is 'pause':
                    self.next_state = 'pause'
                    self.change_state(force_move_on=True)

        elif self.state == 'quit':
            # QUIT experiment
            # DO NOT MODIFY
            if self.singleshot():
                self.clear_screen()
                self.status = False
                self._running = False

        elif self.state == 'pause':
            # PAUSE experiment
            # DO NOT MODIFY
            self.next_state = 'iti'
            self.triggers['pauseRequested'] = False
            if self.singleshot('fast_pause'):
                self.clear_screen()

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
            msg = self.__loading.text
            text = visual.TextStim(self.ptw, pos=(0, 0), text=msg, units="pix", height=30.0)
            text.draw()

        elif self.state == 'idle':
            text = visual.TextStim(self.ptw, pos=(0.0, 0.0), text=self.textToDraw, units="pix", height=30.0)
            text.draw()

        elif self.state == 'quit':
            text = visual.TextStim(self.ptw, pos=(0.0, 0.0), text="Experiment is over", units="pix", height=30.0)
            text.draw()

        elif self.state == 'pause':
            text = 'PAUSE {0}/{1} [Replayed: {2}]'.format(self.trial.nplayed, self.trial.ntrials,
                                                          self.trial.nreplay)
            text = visual.TextStim(self.ptw, pos=(0, 0), text=text, units="pix", height=30.0)
            text.draw()

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


