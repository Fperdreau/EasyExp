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
            n = min([len(data), self._frequency]) - 1
            correct_trials = [trial for trial in data[-n:] if trial[self._field] == 'True']
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
            n = min([len(data), self._frequency]) - 1
            correct_trials = [float(trial[self._field]) for trial in data[-n:]]
            score = np.mean(np.abs(correct_trials))
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

    data = []

    fb = FeedBackContinuous(5, field='response')
    for t in range(50):
        if fb.time_to_update:
            fb.update(data, t)

            data.append({"response": np.random.standard_normal()})
            print(fb)
