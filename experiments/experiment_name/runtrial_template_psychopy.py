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

from psychopy import visual, sound
import pygame
import time
import numpy as np

# EasyExp modules
from core.Core import Core
from core.movie.moviemaker import MovieMaker
from core.buttons.buttons import Buttons
from core.display.fpscounter import FpsCounter
from core.events.timer import Timer

# Multi-threading
import threading

# Custom imports
#################################
# ADD YOUR CUSTOM IMPORTS BELOW #
#################################
from core.misc.conversion import pol2cart, mm2pix
from core.apparatus.sled.mysled import MySled


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

        # Keyboard/Mouse buttons
        # ================
        self.buttons = dict()
        self.responseButton = Buttons(self.ptw, 'mouse', {'left': 0, 'right': 2})

        # Staircase
        # =========
        from core.methods.StaircaseASA.StaircaseASA import StaircaseASA
        self.staircase = StaircaseASA(settings_file=self.trial.design.conditionFile.pathtofile,
                                      data_file=self.user.datafilename)

    def init_devices(self):
        """
        Setup devices
        For better readability of the code, devices should be added to self.devices dictionary.
        Devices should have a close() method, as it is called during the closing routine of the application
        """
        # Create Sled instance
        self.devices['sled'] = MySled(status=self.trial.settings['sled'], server='sled')

        # Create eye-tracker instance
        if self.trial.settings['eyetracker']:
            from core.apparatus.EyeTracker.eyetracker import EyeTracker
            edf_file = "{}_{}".format(self.user.dftName, time.strftime('%d-%m-%Y_%H%M%S'))
            self.devices['eyetracker'] = EyeTracker(link='10.0.0.20', dummy=False, sprate=500, thresvel=35,
                                                    thresacc=9500, illumi=2, caltype='HV5', dodrift=False,
                                                    trackedeye='right', display_type='psychopy', name=edf_file,
                                                    ptw=self.ptw, bgcol=(-1, -1, -1), distance=self.screen.distance,
                                                    resolution=self.screen.resolution,
                                                    winsize=self.screen.size, inner_tgcol=(127, 127, 127),
                                                    outer_tgcol=(255, 255, 255), targetsize_out=1.0, targetsize_in=0.25)
            self.devices['eyetracker'].run()
            self.state = 'calibration'

        # Create OptoTrack
        if self.trial.settings['optotrack']:
            from core.apparatus.optotrack.optotrak import OptoTrack
            self.devices['optotrack'] = OptoTrack()

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
                self.stimuliTrigger[label] = False

            # Send START_TRIAL to eye-tracker
            if self.trial.settings['eyetracker']:
                self.devices['eyetracker'].starttrial(self.trial.id)

            # Initialize movie if requested
            if self.trial.settings['movie']:
                self.movie = MovieMaker(self.ptw, "Dynamic_{}_{}".format(self.trial.params["first"],
                                                                         self.trial.params['timing']), "png")
            # Initialize stimuli
            self.init_stimuli()

            return True

    def init_stimuli(self):
        """
        Prepare/Make stimuli

        Stimuli objects (Psychopy) should be stored in self.stimuli dictionary, for example:
        self.stimuli['stimulus_name'] = visual.Circle(self.ptw, radius=2, pos=(0, 0))

        Then on every loop, the state machine will automatically call self.stimuli['stimulus_name'].draw() if
        self.stimuliTrigger['stimulus_name'] is set to True.
        """
        self.stimuli['stimulus_name'] = None

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
        self.sounds['valid'] = sound.SoundPygame(secs=0.1, value=880)
        self.sounds['valid'].setVolume(1)

        self.sounds['wrong'] = sound.SoundPygame(secs=0.1, value=440)
        self.sounds['wrong'].setVolume(1)

    def quit(self):
        """
        Quit experiment
        :return:
        """
        # Set in idle mode
        self.state = 'idle'
        self.textToDraw = "Experiment is over!"

        # Shutdown the SLED
        for key, device in self.devices.iteritems():
            self.logger.logger.info('[{}] Closing "{}"'.format(__name__, key))
            self.devices[key].close()

        self.status = False

    def go_next(self):
        """
        Check if it is time to move on to the next state. State changes can be triggered by key press (e.g.: ESCAPE key)
        or timers. States' duration can be specified in the my_project_name/experiments/experiment_name/parameters.json
        file.
        :rtype: bool
        """
        # Does the user want to quit the experiment?
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        pygame.event.clear()
        if keys[pygame.K_q]:
            timeToMoveOn = True
            self.triggers['quitRequested'] = True
            return timeToMoveOn

        # Shall we go on?
        if self.timings[self.state] is not False:
            timeToMoveOn = (time.time() - self.state_machine['onset']) >= self.timings[self.state]
        else:
            self.responseButton.get()  # Get buttons status
            timeToMoveOn = self.responseButton.status['left'] or self.responseButton.status['right']

        return timeToMoveOn

    def get_response(self):
        """
        Get participant' response
        """
        # Initialize response timer
        if self.timers['responseDuration'] is None or self.timers['responseDuration'].get_time('start') is None:
            self.timers['responseDuration'] = Timer()
            self.timers['responseDuration'].start()

        # Get response buttons status
        self.responseButton.get()
        response_received = self.responseButton.status['left'] or self.responseButton.status['right']

        if not self.triggers['response_given'] and response_received:
            self.triggers['response_given'] = True

            # Stop response timer, store response duration, and reset timer
            self.timers['responseDuration'].stop()
            self.data['responseDuration'] = round(self.timers['responseDuration'].get_time('elapsed')*1000.0)
            self.timers['responseDuration'].reset()

            # Code response
            self.data['response'] = 'left' if self.responseButton.status['left'] else 'right'
            self.data['correct'] = self.data['response'] == 'right'

    def end_trial(self):
        """
        End trial routine
        :return:
        """
        # Did we get a response from the participant?
        self.validTrial = self.triggers['response_given'] is not False
        self.timers['runtime'].reset()

        # Close movie file is necessary
        if self.trial.settings['movie']:
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

        if 'eyetracker' in self.devices and self.devices['eyetracker'] is not None:
            self.devices['eyetracker'].endtrial(self.validTrial)

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

            # Send events to eye-tracker
            if self.trial.settings['eyetracker']:
                self.devices['eyetracker'].el.sendMessage('EVENT_STATE_{}'.format(self.state))

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

    ################################
    # LINES BELOW CAN BE MODIFIED #
    ################################

    def fast_state_machine(self):
        """
        Real-time state machine: state changes are triggered by keys or timers. States always have the same order.
        This state machine runs at close to real-time speed. Event handlers (key press, etc.) and position trackers
        (optotrack, eye-tracker or sled) should be called within this state machine.
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
                if status:
                    self.stimuli[stim].draw()
        else:
            # Clear screen
            for key, stim in self.stimuli.iteritems():
                stim.setAutoDraw(False)

        # Flip the screen
        self.fpsCounter.flip()

        # Make Movie
        if self.triggers['startTrigger'] and self.trial.settings['movie']:
            self.movie.run()