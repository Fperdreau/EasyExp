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
    from ...apparatus.optotrak.optotrak import OptoTrak
except ImportError as e:
    print(e)
    raise ImportError('Could not import OptoTrak class, but we need it to run the LinearGuide!')

import numpy as np
import logging
import time


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
    _step = 0.01

    def __init__(self, dummy_mode=False, user_file='sample.txt', sensitivity=1.0, velocity_threshold=0.1,
                 time_threshold=0.100, center_from_edge=-0.50, bar_length=1.0, resolution=(1024, 768), axis_index=1):
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
        :param center_from_edge: distance of guide's center from right edge (in m)
        :type center_from_edge: float
        :param bar_length: length of the guide (in m)
        :type bar_length: float
        :param resolution: screen's resolution
        :type resolution: tuple
        :param axis_index: index corresponding to optotrak axis to which the linear guide is aligned
        :type axis_index: int
        """
        self.__velocity_threshold = velocity_threshold
        self.__time_threshold = time_threshold
        self.__user_file = user_file
        self.__dummy_mode = dummy_mode
        self.__center_from_edge = center_from_edge
        self.__bar_length = bar_length
        self.__resolution = resolution
        self.__sensitivity = sensitivity
        self.__axis_index = axis_index

        self.__invalid_sample = None  # Set to time.time() if current sample is NaN

        # Tolerance period during which guide's position will not be updated if received sample is NaN. Beyond this
        # duration an exception will be raised
        self.__invalid_tolerance = 5.0

        self.__tracker = None
        self._position = None
        self._previous = None

        # Initialize tracker
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
        :rtype: bool
        """
        return self.tracker.record()

    def send_message(self, msg):
        """
        Write message into data file
        :param msg: message
        :type msg: str
        :return:
        """
        return self.tracker.send_message(msg)

    @property
    def sensitivity(self):
        return self.__sensitivity

    @sensitivity.setter
    def sensitivity(self, value):
        self.__sensitivity = 0.01 if value < 0.01 else value

    def set_sensitivity(self, direction=-1):
        """
        Increase or decrease sensitivity
        :param direction: increase (=1) or decrease (-1)
        :type direction: int
        """
        self.sensitivity += direction * self._step
        
    @property
    def running(self):
        return self.tracker.running        

    @property
    def position(self):
        """
        Return position of slider in guide coordinates (centered on guide center).
        :rtype: ndarray
        """
        self._previous = self._position

        if not self.__dummy_mode:
            # Position of linear-guide right extremity in optotrak coordinates
            bar = self.tracker.sensors['hand1'].position

            # Position of hand in optotrak coordinates
            hand = self.tracker.sensors['hand2'].position

            # Position of sled's center in optotrak coordinates
            center = np.zeros((1, 3))
            center[0][self.__axis_index] = self.__center_from_edge
            bar_center = bar + center

            # Position of hand relative to world (screen) center
            current_position = hand - bar_center

            # Only set new position if it is valid (not NaN)
            if True not in np.isnan(current_position[0]):
                self.__invalid_sample = None
                self._position = current_position
            else:
                if self.__invalid_sample is None:
                    self.__invalid_sample = time.time()
                    logging.warning("[{}] Current sensor position is not accessible. "
                                    "We use the previous valid position as default".format(__name__))
                elif (time.time() - self.__invalid_sample) >= self.__invalid_tolerance:
                        msg = "[{0}] Sensor position was not accessible for " \
                              "more than {1: 1.0f} seconds. Please, make sure sensors are visible from the Optotrak " \
                              "camera.".format(__name__, self.__invalid_tolerance)
                        logging.fatal(msg)
                        raise Exception(msg)

        else:
            # Get mouse position
            self._position = self.tracker.sensors['hand2'].position

        return self._position

    def __str__(self):
        return 'Position: ({}) | Velocity: {} m/s | Moving: {}'.format(self.position, self.velocity,
                                                                       self.moving)

    @property
    def cursor(self):
        """
        Returns position mapped into screen coordinates and weighted by sensitivity
        Screen coordinates system's origin is set on screen's center.
        x<0: left
        x>0: right
        y<0: bottom
        y>O: top
        :rtype: list (int, int)
        """
        return self.map_screen(self.position)

    def map_screen(self, new_position):
        """
        Returns position mapped into screen coordinates and weighted by sensitivity
        Screen coordinates system's origin is set on screen's center.
        x<0: left
        x>0: right
        y<0: bottom
        y>O: top
        :param new_position: ndarray
        :rtype: list (int, int)
        """
        if not self.__dummy_mode:
            return [int(self.__sensitivity * (new_position[0][self.__axis_index] / (0.5*self.__bar_length))
                        * (0.5 * self.__resolution[0])), 0]
        else:
            return [int(self.__sensitivity * new_position[0]), 0]

    @property
    def delta(self):
        if self._previous is not None:
            return self.map_screen(self.position - self._previous)
        else:
            return [0.0, 0.0]

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
    from psychopy import visual
    import pygame

    # Open window
    win = visual.Window(
        size=(1400, 525),
        monitor='TestMonitor',
        color=(-1, -1, -1),
        units='pix',
        winType='pygame',
        pos=(0, 0),
        waitBlanking=True,
        fullscr=False)
    win.setMouseVisible(False)

    position = np.array((0.0, 0.0))
    cursor = visual.Rect(win, width=50, height=50, fillColor=(0.0, 0.0, 0.0), lineColor=None, units='pix', pos=position)

    try:
        # Instantiate LinearGuide
        guide = LinearGuide(dummy_mode=False, resolution=(1400, 525))
    
        # Print guide position for few seconds
        test_duration = 10.0
        init_time = time.time()
    
        # Example of trial parameters: {parameter_name: parameter_value}
        trial_parameters = {'condition1': 1, 'condition2': 1}
    
        # Start trial
        guide.start_trial(1)
    
        mvt_onset = None
        while (time.time() - init_time) < test_duration:
            if guide.moving and mvt_onset is None:
                mvt_onset = time.time()
                print('Movement has started')
    
            if mvt_onset is not None and not guide.moving:
                mvt_offset = time.time()
                mvt_duration = mvt_offset - mvt_onset
                mvt_onset = None
                print('Movement has ended')
                print('Movement duration: {} s'.format(mvt_duration))
    
            # Update cursor position and render it
            position += guide.delta
            cursor.setPos(position)
            cursor.draw()
    
            text = visual.TextStim(win, text=guide.__str__(), pos=(0, -200))
            text.draw()
            win.flip()
    
            # Record position into a file
            if guide.record():
                # Record stimuli position
                paddle_pos = guide.tracker.position_to_str(cursor.pos)
                guide.tracker.send_message('STIM Paddle {}'.format(paddle_pos))
    
            # Listen to input keys
            pygame.event.pump()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP] or keys[pygame.K_DOWN]:
                if keys[pygame.K_UP]:
                    guide.set_sensitivity(1)
                else:
                    guide.set_sensitivity(-1)
                print('New sensitivity: {}'.format(guide.sensitivity))
    
            if keys[pygame.K_ESCAPE]:
                break
    
        # Stop trial
        guide.stop_trial(1)
    except Exception as e:
        print(e)

    # Close stream
    guide.close()

    # Close Psychopy window
    win.close()
