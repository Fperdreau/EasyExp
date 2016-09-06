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

try:
    from .optotrak.optotrak import OptoTrak
except ImportError:
    raise ImportError('Could not import OptoTrak class, but we need it to run the LinearGuide!')

import numpy as np


class LinearGuide(object):
    """
    Wrapper class of Optotrak class made to ease the use of the linear guide.
    Guide position (or slider position) is coded relative to the linear-guide center (x<0: left, x>0: right).
    This class implements few common methods with the Optotrak class:
    - start_trial() - start trial routine
    - stop_trial() - stop trial routine
    - close() - closing routine
    - record() - record sensor position into file
    - init() - Initialize Optotrak

    However, all Optotrak class' methods can be directly access by calling LinearGuide.tracker.__method_name__()
    """

    sensors_label = ('Xas', 'Marker2', 'Yas', 'origin', 'hand1', 'hand2')  # Sensors label
    center_from_edge = -0.50  # Distance of guide center from right edge (in m)

    def __init__(self, dummy_mode=False, user_file='sample.txt', sensitivity=1.0, velocity_threshold=0.1,
                 time_threshold=0.100, center_from_edge=None):
        """
        LinearGuide constructor
        :param dummy_mode: dummy mode enabled
        :type dummy_mode: bool
        :param user_file: path to data file
        :type user_file: str
        :param sensitivity: mapping sensitivity
        :type sensitivity: float
        :param velocity_threshold: velocity threshold for movement detection (in m/s)
        :type velocity_threshold: float
        :param time_threshold: time window over which a sensor must stay at the same location to be considered as stable
        (in seconds)
        :type time_threshold: float
        """
        self.__sensitivity = sensitivity
        self.__velocity_threshold = velocity_threshold
        self.__time_threshold = time_threshold
        self.__user_file = user_file
        self.__dummy_mode = dummy_mode

        if center_from_edge is not None:
            self.center_from_edge = center_from_edge

        self.__tracker = None
        self.init()

    @property
    def tracker(self):
        """
        Factory: Get Optotrak instance
        :rtype: OptoTrak
        """
        if self.__tracker is None:
            self.__tracker = OptoTrak(user_file=self.__user_file, freq=200.0,
                                      velocity_threshold=self.__velocity_threshold,
                                      time_threshold=self.__time_threshold,
                                      labels=LinearGuide.sensors_label,
                                      dummy_mode=self.__dummy_mode,
                                      tracked=self.sensors_label)
        return self.__tracker

    def init(self):
        """
        Initialize Optotrack
        :return: void
        """
        self.tracker.init()

    def start_trial(self, trial_id, params=None):
        """
        Start trial routine
        :param trial_id: trial id
        :type trial_id: int
        :param params: trial's parameters
        :type params: dict
        :return: void
        """
        self.tracker.start_trial(trial=trial_id, param=params)

    def stop_trial(self, trial_id, valid=True):
        """
        Stop trial routine
        :param trial_id: trial's id
        :type trial_id: int
        :param valid: trial validity
        :type valid: bool
        :return: void
        """
        self.tracker.stop_trial(trial=trial_id, valid=valid)

    def close(self):
        """
        Closing routine
        :return: void
        """
        self.tracker.close()

    def record(self):
        """
        Record into data file
        :return: void
        """
        self.tracker.record()

    @property
    def position(self):
        """
        Return position of slider in guide coordinates (centered on guide center).
        :rtype: ndarray
        """
        if not self.__dummy_mode:
            # Position of linear-guide right extremity in optotrak coordinates
            bar = self.tracker.sensors['hand1'].position

            # Position of hand in optotrak coordinates
            hand = self.tracker.sensors['hand2'].position

            # Position of sled's center in optotrak coordinates
            bar_center = bar + np.array((0.0, self.center_from_edge, 0.0))

            # Position of hand relative to world (screen) center
            return hand - bar_center
        else:
            return self.tracker.sensors['hand2'].position

    @property
    def velocity(self):
        """
        Return sensor's velocity
        :return:
        """
        return self.tracker.sensors['hand2'].velocity

    @property
    def moving(self):
        """
        Return movement state
        :return:
        """
        return self.velocity >= self.__velocity_threshold

    def valideposition(self):
        """
        Validate end position of sensor: sensor must not move for a given duration to be considered as stable
        """
        return self.tracker.sensors['hand2'].validposition()

    def checkposition(self, (x, y, z), radius):
        """
        Check that the tracked hands are located within a range from a given position
        :param radius:
        :return:
        """
        ref_position = np.array((x, y, z))
        distance = OptoTrak.distance(ref_position, self.position)
        return distance <= radius

if __name__ == '__main__':
    import time

    # Instantiate LinearGuide
    guide = LinearGuide(dummy_mode=False)

    # Print guide position for few seconds
    test_duration = 5.0
    init_time = time.time()

    # Example of trial parameters: {parameter_name: parameter_value}
    trial_parameters = {'condition1': 1, 'condition2': 1}

    # Start trial
    guide.start_trial(1)
    mvt_onset = None
    while (time.time() - init_time) < test_duration:
        print('Position: {} | Velocity: {} | Moving: {}'.format(guide.position, guide.velocity, guide.moving))
        # Record date into file
        guide.record()

        if guide.moving and mvt_onset is None:
            mvt_onset = time.time()
            print('Movement has started')

        if mvt_onset is not None and not guide.moving:
            mvt_offset = time.time()
            mvt_duration = mvt_offset - mvt_onset
            print('Movement has ended')
            print('Movement duration: {} s'.format(mvt_duration))
            break

    # Stop trial
    guide.stop_trial(1)

    # Close stream
    guide.close()