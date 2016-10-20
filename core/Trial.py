#!/usr/bin/env python
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

from __future__ import print_function

# IMPORTS
# =======
# Core
from Design import Design
from Config import ConfigFiles
from core.events.pause import Pause
from core.methods.MethodContainer import MethodContainer

# Import useful libraries
import time
from os.path import isfile

# Data I/O
import csv

# Logger
import logging


class Trial(object):
    """
    Trial class
    Handles trial information, status, and routines
    Methods:
        - replay(): replays the trial, indicates in the data file which trial has been replayed, move the trial to the
         end of the trial list
        - getResponse(): get subject's response, only listen to predefined keys.
        - showFeedback(): Display a feedback according to the user's response.
    """

    def __init__(self, design=Design, settings=None, userfile='', paramsfile=None, pause_interval=0):
        """
        Constructor of Trial class
        :param string paramsfile: path to parameter file
        :param Design design: instance of Design class
        :param settings: Experiment's settings
        :type settings: dict
        :param userfile: user data file's name
        :param pause_interval: time interval between pauses (in seconds. 0: no pause)
        """

        self.design = design
        self.settings = settings
        self.userfile = userfile
        self.__logger = logging.getLogger('EasyExp')

        # Initialize attributes
        self.id = 0  # Trial ID
        self.nreplay = 0  # Number of trials replayed so far
        self.nplayed = 0  # Number of valid trials played so far
        self.data = []
        self.replayed = True  # Can be True/False/"replay"
        self.status = True  # Experiment's status (False if over)

        # Lists
        self.played = []  # List of played trials
        self.params = {}  # Trial's parameters.json
        self.__playlist = []  # List of trials to play
        self.__replay_list = []  # List of trials to replay
        self.__default_fields = {}

        # Timers
        self.init_time = 0
        self.end_time = 0

        # Pause
        self.pauseInt = pause_interval  # Pause interval
        self.pause_time = None
        self.nbPause = 0
        self.pause = Pause(mode=settings['setup']['pauseMode'], interval=settings['setup']['pauseInt'])

        # Load Trials list
        self.__random_design = None

        # Load conditions
        self.conditions = design.allconditions
        self.ntrials = design.ntrials  # Total number of trials to play

        # Load experiment's parameters
        self.__paramsfile = paramsfile
        self.parameters = Trial.get_params(paramsfile)

        # Experiment method
        self.method = MethodContainer(method=self.conditions['method'],
                                      settings_file=self.design.conditionFile.pathtofile, data_file=self.userfile,
                                      options=self.conditions['options'])

    def __str__(self):
        """
        Print method of Trial
        :return: string
        """
        return "\n--- Trial Information ---\n" \
               "\tID: {0}\n" \
               "\tPlayed: {1}\{2}\n" \
               "\tReplayed: {3}\n" \
               "\tParams: {4}\n".format(self.id, self.nplayed, self.ntrials, self.nreplay, self.params)

    def run_pause(self, force=False):
        """
        Is it time to do a break?
        :param force: manually trigger pause
        :type force: bool
        :return: Is a pause required?
        :rtype: bool
        """
        if self.pause.run(force=force):
            self.__logger.info('[{0}] {1}'.format(__name__, self.pause.text))
            return True
        else:
            return False

    @staticmethod
    def get_params(paramsfile):
        """
        Get experiment's parameters
        :param string paramsfile: full path to parameters.json file
        :return:
        """
        if paramsfile is not None:
            paramsfile = ConfigFiles(paramsfile)
            parameters = paramsfile.load()
        else:
            parameters = {}
        return parameters

    def __load_design(self):
        """
        Loads and randomizes trials list
        :return void:
        """
        self.__random_design = None
        self.design.load()

        design = []
        for t in self.design.design:
            design.append(t)

        # Remove played trials from trials list
        self.__random_design = Trial.filter_design(self.design.design)

    def setup(self):
        """
        Setup of the trial
        :return self.status: Trial's status (True, False or 'pause')
        """
        self.replayed = True
        self.parameters = Trial.get_params(self.__paramsfile)

        # Get trial to play
        self.__load_design()
        self.id = self.get_trial_id()
        self.status = self.id is not False

        if self.run_pause():
            self.status = 'pause'
        else:
            if self.id is not False:
                self.params = self.design.get_trial(self.id)
                self.start()
                self.status = True
            else:
                self.__logger.info('\n[{}] The experiment is over!'.format(__name__))
                self.status = False
        return self.status

    def get_trial_id(self):
        """
        Get next trial ID
        :return: int or boolean
        """
        self.get_playlist()
        self.load_data()

        if len(self.__playlist) > 0:
            self.id = self.__playlist[0]
        else:
            self.id = False
        return self.id

    @staticmethod
    def filter_design(design):
        """
        This function removes successfully played trials from the trials list
        :param list design: trials list
        :type design: list(dict)
        :return:
        """
        filtered_design = [design[ii] for ii in range(len(design)) if design[ii]['Replay'] != 'False']
        return filtered_design

    def get_playlist(self):
        """
        Get list of trials to replay
        :return:
        """
        self.played = []
        self.__playlist = []
        self.__replay_list = []
        for trial in self.__random_design:
            if trial['Replay'] == 'True':
                self.__playlist.append(int(trial['TrialID']))
            elif trial['Replay'] == 'replay':
                self.__replay_list.append(int(trial['TrialID']))

        self.nplayed = self.design.ntrials - len(self.__random_design)
        if len(self.__playlist) == 0 and len(self.__replay_list) > 0:
            self.__playlist = self.__replay_list

    def parse(self, params):
        """
        Parse trial's parameters.json
        :param params:
        :return:
        """
        i = 0
        self.params = {}
        for condition in self.design.conditions:
            self.params[condition] = params[i]
            i += 1

    def start(self):
        """
        Start the trial and the timer
        :return:
        """
        self.init_time = time.time()
        self.__logger.info(self)

    def __valid(self):
        """
        Valid trial
        :return:
        """
        self.replayed = False
        self.design.update(self.id, {'Replay': False})
        self.design.save(True)

    def stop(self, status):
        """
        Ends the trial and report its total duration
        :return:
        """
        if not status:
            self.__replay()
        else:
            self.__valid()
        self.end_time = time.time() - self.init_time
        self.__logger.info("[{0}] Trial {1}: END (duration: {2:.2f})".format(__name__, self.id, self.end_time))

    def __replay(self):
        """
        Replay this trial: Indicate in the data file that this trial has been replayed and append the trial to the end
        of the file
        :return: bool
        """
        self.__logger.info('[{}] Trial {} => INVALID!'.format(__name__, self.id))
        self.nreplay += 1
        self.replayed = 'replay'
        self.design.update(self.id, {'Replay': 'replay'})
        self.design.save(True)

    def openfile(self):
        """
        Create user's data file and write header's fields:
         Basic fields: TrialID, replayed, conditions (Provided by defaultfieldsname),
            measures (keep the conditions' order for convenience)
        """
        if not isfile(self.userfile):
            try:
                with open(self.userfile, 'w', 0) as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=self.__default_fields)
                    writer.writeheader()
            except (IOError, TypeError) as e:
                msg = IOError("[{}] Could not write into the user's datafile '{}': {}".format(
                    __name__, self.userfile, e))
                self.__logger.critical(msg)
                raise msg

    def write_data(self, datatowrite=None):
        """
        Write user's data to the data file (may be call at the end of each trial)
        :param datatowrite: list of data to write.
        :type datatowrite: None|dict
        """
        data = {'TrialID': self.id, 'Replay': self.replayed}
        data.update(self.params)
        if datatowrite is not None:
            data.update(datatowrite)
        self.__default_fields = data.keys()

        if not isfile(self.userfile):
            self.__logger.warning('[{}] User Data filename does not exist yet. We start from scratch!'.format(__name__))
            self.openfile()
        try:
            with open(self.userfile, 'a') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.__default_fields)
                writer.writerow(data)
        except (IOError, TypeError) as e:
            msg = IOError('[{}] User Data filename could not be read: {}'.format(__name__, e))
            self.__logger.critical(msg)
            raise msg

    def load_data(self):
        """
        Load data from file
        :return:
        """
        data = []
        try:
            with open(self.userfile) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data.append(row)
        except (IOError, TypeError):
            self.__logger.warning('[{}] User Data filename does not exist yet'.format(__name__))
        return data
