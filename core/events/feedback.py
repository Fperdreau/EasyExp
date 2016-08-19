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
        self.count = 0
        self.frequency = frequency
        self.field = field
        self.prev_score = 0.0
        self.msg = ''

    def timeToUpdate(self):
        """
        Check if it is time to show a feedback
        :return: True if is time to update. False otherwise
        """
        self.count += 1
        print('Feedback count: {}'.format(self.count))
        do_update = self.count >= self.frequency
        if do_update:
            self.count = 0
        return do_update

    def getFeedBack(self, data, nplayed):
        """
        Get feedback message indicating current score and progression since last feedback
        :param data: data array
        :type data: array-like (trial x property)
        :param nplayed: number of played trials
        :type nplayed: int
        :return str msg: message to display
        """
        if len(data) > 0 and nplayed > 0:
            correct_trials = [data[ii] for ii in range(len(data)) if data[ii][self.field] == 'True']
            nCorrect = len(correct_trials)
            score = (nCorrect/nplayed) * 100.0
            progression = ((score - self.prev_score) / self.prev_score) * 100
        else:
            score = 0.0
            progression = 0.0

        self.prev_score = score
        self.msg = 'Score: {0: 1.1f}% | Progression: {1:1.1f}%'.format(score, progression)
        print(self.msg)
        return self.msg
