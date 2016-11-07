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

import logging
import numpy as np

_version_ = "1.1.0"


class FeedBack(object):
    """
    Feedback class: generates performance feedback displayed to participants
    """

    def __init__(self, frequency=20, field='correct'):
        """
        Feedback constructor

        :param frequency: frequency of feedback (every n trials)
        :type frequency: int
        :param field: "correct response" field in data array
        :type field: str
        """
        self._count = 0
        self._frequency = frequency
        self._field = field
        self._prev_score = 0.0
        self._score = 0.0
        self._progression = 0.0
        self._msg = None

    @property
    def time_to_update(self):
        """
        Check if it is time to show a feedback
        :return: True if is time to update. False otherwise
        """
        self._count += 1
        do_update = self._count >= self._frequency
        logging.getLogger('EasyExp').info('Feedback: {}({})'.format(do_update, self._count))

        if do_update:
            self._count = 0
        return do_update

    @property
    def progression(self):
        """
        Compute progression since last feedback
        :return:
        """
        if self._prev_score != 0.0:
            self._progression = ((self._score - self._prev_score) / self._prev_score) * 100.0
        else:
            self._progression = 0.0
        return self._progression

    @property
    def msg(self):
        self._msg = self.__str__()
        return self._msg

    @property
    def score(self):
        return self._score

    def update(self, data, played):
        """
        Get feedback message indicating current score and progression since last feedback
        :param data: data array
        :type data: array-like (trial x property)
        :param played: number of played trials
        :type played: int
        :return void
        """

        if len(data) > 0 and played > 0:
            correct_trials = [data[ii] for ii in range(len(data)) if data[ii][self._field] == 'True']
            n_correct = float(len(correct_trials))
            score = (n_correct / float(played)) * 100.0
        else:
            score = 0.0

        self._prev_score = self._score
        self._score = score

    def __str__(self):
        return 'Score: {0: 1.1f}% | Progression: {1:1.1f}%'.format(self._score, self.progression)


class FeedBackContinuous(FeedBack):
    """
    Extension of Feedback class to support continuous measurements
    """

    def update(self, data, played):
        """
        Get feedback message indicating current score and progression since last feedback
        :param data: data array
        :type data: array-like (trial x property)
        :param played: number of played trials
        :type played: int
        :return void
        """

        if len(data) > 0 and played > 0:
            correct_trials = [float(data[ii][self._field]) for ii in range(len(data))]
            score = np.mean(correct_trials)
        else:
            score = 0.0

        self._prev_score = self._score
        self._score = score

    def __str__(self):
        return 'Score: {0: 1.1f} | Progression: {1:1.1f}%'.format(self._score, self.progression)


if __name__ == '__main__':

    data = []
    fb = FeedBack(5)

    for t in range(50):
        if fb.time_to_update:
            fb.update(data, t)
            print(fb)

        if np.random.random() >= 0.5:
            correct = 'True'
        else:
            correct = 'False'
        data.append({'correct': correct})

    all_data = [{'landmark_status': '1', 'mvt': 'True', 'side': 'left', 'Replay': 'False', 'landmark_side': '1', 'TrialID': '17',
      'response': '96.591607869660436', 'landmark_distance': '100'},
     {'landmark_status': '1', 'mvt': 'True', 'side': 'right', 'Replay': 'False', 'landmark_side': '-1', 'TrialID': '42',
      'response': '-108.35165428884542', 'landmark_distance': '-1'},
     {'landmark_status': '1', 'mvt': 'True', 'side': 'left', 'Replay': 'False', 'landmark_side': '1', 'TrialID': '57',
      'response': '253.57736661891465', 'landmark_distance': '100'},
     {'landmark_status': '1', 'mvt': 'True', 'side': 'right', 'Replay': 'False', 'landmark_side': '-1',
      'TrialID': '226', 'response': '-44.954378875942616', 'landmark_distance': '50'},
     {'landmark_status': '1', 'mvt': 'True', 'side': 'left', 'Replay': 'False', 'landmark_side': '1', 'TrialID': '291',
      'response': '123.23584900561099', 'landmark_distance': '-1'},
     {'landmark_status': '1', 'mvt': 'True', 'side': 'right', 'Replay': 'False', 'landmark_side': '1', 'TrialID': '380',
      'response': '77.278286187005889', 'landmark_distance': '200'},
     {'landmark_status': '1', 'mvt': 'True', 'side': 'left', 'Replay': 'False', 'landmark_side': '-1', 'TrialID': '163',
      'response': '23.545132241295534', 'landmark_distance': '0'},
     {'landmark_status': '1', 'mvt': 'True', 'side': 'right', 'Replay': 'False', 'landmark_side': '-1',
      'TrialID': '242', 'response': '-56.710505329889614', 'landmark_distance': '-1'},
     {'landmark_status': '1', 'mvt': 'True', 'side': 'left', 'Replay': 'False', 'landmark_side': '-1', 'TrialID': '221',
      'response': '127.06889654653492', 'landmark_distance': '-1'},
     {'landmark_status': '1', 'mvt': 'True', 'side': 'right', 'Replay': 'False', 'landmark_side': '1', 'TrialID': '100',
      'response': '74.534348734929978', 'landmark_distance': '200'},
     {'landmark_status': '1', 'mvt': 'True', 'side': 'left', 'Replay': 'False', 'landmark_side': '1', 'TrialID': '295',
      'response': '25.993236024661659', 'landmark_distance': '50'},
     {'landmark_status': '1', 'mvt': 'True', 'side': 'right', 'Replay': 'False', 'landmark_side': '1', 'TrialID': '134',
      'response': '-37.124957569462985', 'landmark_distance': '0'},
     {'landmark_status': '1', 'mvt': 'True', 'side': 'left', 'Replay': 'False', 'landmark_side': '1', 'TrialID': '275',
      'response': '12.401668129059871', 'landmark_distance': '50'},
     {'landmark_status': '1', 'mvt': 'True', 'side': 'right', 'Replay': 'False', 'landmark_side': '-1',
      'TrialID': '144', 'response': '87.055586652654227', 'landmark_distance': '0'},
     {'landmark_status': '1', 'mvt': 'True', 'side': 'left', 'Replay': 'False', 'landmark_side': '-1', 'TrialID': '205',
      'response': '-107.02315708640468', 'landmark_distance': '50'},
     {'landmark_status': '1', 'mvt': 'True', 'side': 'right', 'Replay': 'False', 'landmark_side': '1', 'TrialID': '200',
      'response': '66.433153579148382', 'landmark_distance': '200'}]

    fb = FeedBackContinuous(5, field='response')
    for t in range(len(all_data)):
        if fb.time_to_update:
            data = [all_data[ii] for ii in range(0, t)]
            fb.update(data, t)
            print(fb)
