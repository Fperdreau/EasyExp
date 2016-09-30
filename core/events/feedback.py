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
        print('Feedback count: {}'.format(self._count))
        do_update = self._count >= self._frequency
        if do_update:
            self._count = 0
        return do_update

    @property
    def progression(self):
        """
        Compute progression since last feedback
        :return:
        """
        self._progression = ((self._score - self._prev_score) / self._prev_score) * 100.0
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
            n_correct = len(correct_trials)
            score = (n_correct / played) * 100.0
        else:
            score = 0.0

        self._prev_score = self._score
        self._score = score

    def __str__(self):
        return 'Score: {0: 1.1f}% | Progression: {1:1.1f}%'.format(self._score, self._progression)
