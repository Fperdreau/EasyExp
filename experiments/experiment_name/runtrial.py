#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of EasyExp
#
# Copyright (C) 2015 Florian Perdreau, Radboud University Nijmegen
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
from __future__ import print_function
from __future__ import division

from psychopy import visual, sound
import time
import numpy as np

# EasyExp modules
from core.Core import Core
from core.misc.conversion import pol2cart, mm2pix
from core.movie.moviemaker import MovieMaker
from core.buttons.buttons import Buttons
from core.display.fpscounter import FpsCounter
from core.events.timer import Timer

# Multi-threading
import threading

# Custom imports
from core.apparatus.sled.mysled import MySled


class RunTrial(object):
    """
    RunTrial class
    This class handles experiment's trials procedure

    """

    homeMsg = 'Welcome!'  # Message prompted at the beginning of the experiment

    def __init__(self, core=Core):
        """
        Class constructor

        Parameters
        ----------
        :param Core core: Core object
        :type core: Core
        """

        ##################################
        # DO NOT MODIFY THE LINES BELLOW #
        ##################################
        self.core = core
        self.screen = core.screen
        self.trial = core.trial
        self.user = core.user
        self.ptw = self.screen.ptw
        self.textToDraw = RunTrial.homeMsg

        # State Machine
        # =============
        self.state_machine = {
            'current': None,
            'status': False,
            'timer': None,
            'duration': 0.0,
            'onset': 0.0,
            'offset': 0.0
        }
        self.status = True
        self.state = 'idle'
        self.nextState = "iti"
        self.singleShot = True  # Enable single shot events
        self.validTrial = False

        # Dependencies
        # ============
        # FPScounter: measures flip duration or simply flips the screen
        self.fpsCounter = FpsCounter(self.screen.ptw)

        # Logger: verbose level can be set by changing level to 'debug', 'info' or 'warning'
        self.logger = core.logger

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
        # Sled settings
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

        # Response buttons
        # ================
        self.buttons = dict()
        self.buttons['gui'] = Buttons(self.ptw, 'keyboard', {'quit': 'esc'})
        self.buttons['response'] = Buttons(self.ptw, 'mouse', {'left': 0, 'right': 2})

        # Staircase
        # =========
        from core.methods.StaircaseASA.StaircaseASA import StaircaseASA
        self.staircase = StaircaseASA(settings_file=self.trial.design.conditionFile.pathtofile,
                                      data_file=self.user.datafilename)

    def init_devices(self):
        """
        Setup devices
        """
        # Create Sled instance
        self.devices['sled'] = MySled(status=self.trial.settings['sled'], server='sled')

        # Create Eyelink instance
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

    def init(self):
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
        self.devices['sled'].quit()

        # Shutdown eye-tracker
        if self.trial.settings['eyetracker']:
            self.devices['eyetracker'].close()

        self.status = False

    @property
    def move_on(self):
        """
        Go to next state if SPACE button is pressed or quit experiment if ESCAPE button is pressed
        :rtype: bool
        """
        if self.triggers['moveOnRequested']:
            self.triggers['moveOnRequested'] = False
            return True

        # Does the user want to quit the experiment?
        if self.buttons['gui'].status['quit']:
            self.triggers['quitRequested'] = True
            return True
        elif self.buttons['gui'].status['pause']:
            self.triggers['pauseRequested'] = True
            return True

        # Shall we go on?
        if self.timings[self.state] is not False:
            return self.state_machine['timer'].countdown() > 0.0
        else:
            self.buttons['response'].get()  # Get buttons status
            return self.buttons['response'].status['left'] or self.buttons['response'].status['right']

    def get_response(self):
        """
        Get subject response
        :return response: 'left' or 'right'
        """
        if self.timers['responseDuration'] is None:
            # Initialize response timer
            self.timers['responseDuration'] = Timer()
            self.timers['responseDuration'].start()

        # Get response buttons status
        self.buttons['response'].get()
        response_received = self.buttons['response'].status['left'] or self.buttons['response'].status['right']
        if not self.triggers['response_given'] and response_received:
            if self.buttons['response'].status['left']:
                self.data['response'] = 'left'
            elif self.buttons['response'].status['right']:
                self.data['response'] = 'right'

            # Stop response timer, store response duration, and reset timer
            self.timers['responseDuration'].stop()
            self.data['responseDuration'] = self.timers['responseDuration'].get_time('elapsed')
            self.timers['responseDuration'].reset()

            self.data['correct'] = self.data['response'] == 'right'
            self.triggers['response_given'] = True

    def end_trial(self):
        """
        End trial routine
        :return:
        """
        self.validTrial = self.data['response'] is not False

        # Close movie file is necessary
        if self.trial.settings['movie']:
            self.movie.close()

        # Replay the trial if the user did not respond fast enough or moved the hand before the response phase
        self.logger.logger.info('### Trial {} Results:'.format(self.trial.id))
        for data, value in self.data.iteritems():
            self.logger.logger.info('{}: {}'.format(data, value))
        self.logger.logger.info('valid trial:{}'.format(self.validTrial))

        # Play an auditory feedback to inform whether the trial was valid or not
        if not self.validTrial:
            self.sounds['wrong'].play()
        else:
            self.sounds['valid'].play()

        self.trial.stop(self.validTrial)  # Stop routine
        self.trial.writedata(self.data)  # Write data

        if self.trial.settings['eyetracker']:
            self.devices['eyetracker'].endtrial(self.validTrial)

    # =========================================
    # SLED movement
    # =========================================
    @property
    def viewer_position(self):
        """
        Get viewer (sled) position
        """
        if self.devices['sled'] is not None:
            p = self.devices['sled'].getposition(t=self.devices['sled'].client.time())
            return p[0], p[1]
        else:
            return 0.0, 0.0

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

    def change_state(self, force_move_on=False):
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
            self.state_machine['onset'] = self.state_machine['timer'].get('start')
            self.state_machine['status'] = True
            self.singleShot = True  # Enable single shot events

            # Send events to eye-tracker
            if self.trial.settings['eyetracker']:
                self.devices['eyetracker'].el.sendMessage('EVENT_STATE_{}'.format(self.state))

        # If we transition to the next state
        if force_move_on or (self.move_on and self.state_machine['status']):
            # Stop timer, store timings and then reset timer
            self.state_machine['timer'].stop()
            self.state_machine['offset'] = self.state_machine['timer'].get('stop')
            self.state_machine['duration'] = self.state_machine['timer'].get('elapsed')
            self.state_machine['timer'].reset()

            self.state_machine['status'] = False

            state_str = '[STATE]: {0}=>{1}' \
                        ' [START: {2:.3f}s | DUR: {3:.3f}s]\r'.format(self.state, self.nextState,
                                                                      self.state_machine['onset'] -
                                                                      self.timers['runtime'].get_time('start'),
                                                                      self.state_machine['duration'])
            self.logger.logger.info(state_str)
            self.state = self.nextState
            self.state_machine['current'] = None
            return True
        else:
            return False

    ################################
    # LINES BELLOW CAN BE MODIFIED #
    ################################

    def fast_state_machine(self):
        """
        Fast state machine

        Returns
        -------
        void
        """
        while self.status:
            tic = time.time()

            # Check state status
            self.change_state()

            if self.state == 'idle':
                """
                IDLE state
                DO NOT MODIFY
                """
                self.nextState = 'iti'

            elif self.state == 'quit':
                # QUIT experiment
                # DO NOT MODIFY

                if self.singleShot:
                    self.singleShot = False
                    self.quit()

            elif self.state == 'pause':
                # PAUSE experiment
                # DO NOT MODIFY
                self.nextState = 'iti'
                if self.singleShot is True:
                    self.singleShot = False
                    self.triggers['pauseRequested'] = False

                    # Move the sled back to its default position
                    self.devices['sled'].move(self.sledHome, self.mvtBackDuration)
                    time.sleep(self.mvtBackDuration)
                    self.devices['sled'].lights(True)  # Turn the lights off

            elif self.state == 'calibration':
                # Eyetracker calibration
                self.nextState = 'iti'

            elif self.state == 'iti':
                # Inter-trial interval
                self.nextState = 'start'
                if self.singleShot is True:
                    self.singleShot = False
                    if self.devices['sled'] is not None:
                        self.devices['sled'].lights(False)  # Turn the lights off

            elif self.state == 'start':
                # Start trial: get trial information and update trial's parameters accordingly
                self.nextState = 'first'

                if self.singleShot is True:
                    self.singleShot = False
                    status = self.init()  # Get trial parameters
                    if not status:
                        self.nextState = 'quit'
                        self.triggers['moveOnRequested'] = True
                    if status is 'pause':
                        self.nextState = 'pause'
                        self.triggers['moveOnRequested'] = True
                        self.triggers['pauseRequested'] = True
                        self.data['response'] = False

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
                    if np.abs(self.viewer_position[0] - self.sledStart) > 0.01:
                        self.logger.logger.debug('Sled is not at starting position: {}'
                                                 ' instead of {}'.format(self.viewer_position[0], self.sledStart))
                        self.devices['sled'].move(self.sledStart, self.mvtBackDuration)
                        self.timings['start'] = self.mvtBackDuration + 0.1
                        time.sleep(self.mvtBackDuration)
                        self.logger.logger.debug('Sled after move command: {}'.format(self.viewer_position[0]))
                    else:
                        self.timings['start'] = 0.1

            elif self.state == 'first':
                self.nextState = 'probe1'
                if self.singleShot is True:
                    self.singleShot = False
                    self.timers['sled_start'] = time.time()
                    self.devices['sled'].move(self.sledFinal, self.mvtDuration)

            elif self.state == 'probe1':
                self.nextState = 'probeInterval'
                self.stimuliTrigger['probe1'] = True
                if self.singleShot is True:
                    self.singleShot = False
                    self.data['sled_probe1'] = self.viewer_position[0]
                    self.data['time_probe1'] = time.time() - self.timers['sled_start']
                    self.logger.logger.debug('Sled Position at probe1: {}'.format(self.data['sled_probe1']))

            elif self.state == 'last':
                self.nextState = 'response'
                self.stimuliTrigger['probe2'] = False

            elif self.state == 'response':
                self.get_response()
                self.nextState = 'end'

                if self.triggers['response_given']:
                    if self.trial.params['mvt'] == 'True':
                        # If dynamic, we wait until the sled reaches its final position
                        if (time.time() - self.timers['sled_start'].get_time('start'))\
                                >= self.trial.parameters['movDuration']:
                            self.triggers['moveOnRequested'] = True
                    else:
                        self.triggers['moveOnRequested'] = True

            elif self.state == 'end':
                if self.triggers['pauseRequested']:
                    self.nextState = "pause"
                elif self.triggers['quitRequested']:
                    self.nextState = "quit"
                else:
                    self.nextState = 'iti'

                if self.singleShot is True:
                    self.singleShot = False
                    self.triggers['startTrigger'] = False
                    self.triggers['response_given'] = False

                    # Clear screen
                    for key, stim in self.stimuli.iteritems():
                        stim.setAutoDraw(False)

                    # End trial routine
                    self.end_trial()

            toc = time.time() - tic
            print('[{}] Elapsed time: {} ms'.format(__name__, round(toc*1000.0)))

    def graphics_state_machine(self):
        """
        Graphical (slow) state machine: running speed of this state machine is limited by the screen's refresh rate. For
        instance, this state machine will be updated every 17 ms with a 60Hz screen. For this reason, only slow events
        (display of stimuli) should be described here. Everything that requires faster (close to real-time) processing
        should be specified in the fast_state_machine method.

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
            if self.singleShot:
                self.singleShot = False
                # Create calibration points (polar grid, with points spaced by 45 degrees)
                x, y = pol2cart(0.25 * (self.screen.resolution[0] / 2), np.linspace(0, 2 * np.pi, 9))
                x += 0.5 * self.screen.resolution[0]  # Center coordinates on screen center
                y += 0.5 * self.screen.resolution[1]

                # Start calibration
                self.devices['eyetracker'].calibration.custom_calibration(x=x, y=y, ctype='HV9')
                self.devices['eyetracker'].calibration.calibrate()

        ##################################
        # DO NOT MODIFY THE LINES BELLOW #
        ##################################
        # Draw stimuli
        if self.triggers['startTrigger']:
            fixation_position = mm2pix(1000 * self.viewer_position[0], 0.0, self.screen.resolution, self.screen.size)
            self.stimuli['fixation'].setPos(fixation_position)  # Update fixation position
            for stim, status in self.stimuliTrigger.iteritems():
                if status:
                    self.stimuli[stim].draw()

        # Flip the screen
        self.fpsCounter.flip()

        # Make Movie
        if self.triggers['startTrigger'] and self.trial.settings['movie']:
            self.movie.run()
