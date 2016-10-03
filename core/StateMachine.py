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

from events.timer import Timer
import time

# Logger
import logging


class StateMachine(object):
    """
    State class
    Implement state of state machine
    """

    def __init__(self, timings=dict, logger=None):
        """
        State constructor
        Parameters
        ----------
        :param timings: dictionary specifying states timings (in seconds)
            if duration is False, then the state machine will stay within the same state until told otherwise
            if duration is 0.0, then the state machine will immediately move to the next state
            if duration is float > 0.0, then the state machine will stay in the same state for the given duration
        :type timings: dict
        :param logger: application logger
        :type logger: logging|Customlogger
        """
        self.__durations = timings

        self._state = None
        self._current = None
        self._next_state = None

        self.logger = logger if logger is not None else logging.getLogger("EasyExp")

        self._runtime = Timer()
        self._runtime.start()

    @property
    def current(self):
        return self._current

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        self._state = new_state

    @property
    def next_state(self):
        return self._next_state

    @next_state.setter
    def next_state(self, next_state):
        self._next_state = next_state

    @property
    def durations(self):
        return self.__durations

    @durations.setter
    def durations(self, timings):
        """
        Update timings or set new timings
        :param timings:
        :type timings: dict
        :return:
        """
        self.__durations.update(timings)

    def singleshot(self, name='default', target=None, **kwargs):
        """
        Fire singleshot event
        :param name: event's label
        :param target: target function (optional)
        :param kwargs: function arguments (optional)
        :rtype: bool
        """
        if self.current is not None:
            return self.current.singleshot(name=name, target=target, **kwargs)
        else:
            return False

    def start(self):
        """
        This function handles transition between states
        DO NOT MODIFY
        :rtype: bool
        """
        # If we enter a new state
        self._current = State(self.state, duration=self.__durations[self.state])
        self._current.start()
        msg = "[{0}] '{1}' state starting [t={2:1.3f}]".format(__name__,
                                                               self.state.upper(), self.current.start_time
                                                               - self._runtime.get_time('start'))
        self.logger.info(msg)

    def stop(self):
        """
        Move to next state
        :return:
        """
        if self.current is not None:
            self.current.stop()
            self.logger.info(self)
            self.state = self.next_state

    def change_state(self, force_move_on=False):
        """
        This function handles transition between states
        DO NOT MODIFY
        :rtype: bool
        """
        if self.current is None:
            # If we enter a new state
            self.start()
            return True

        # If we transition to the next state
        if force_move_on or (self._current.status and self._current.running):
            self.stop()
            self.start()
            return True
        else:
            return False

    def __str__(self):
        return '[{0}]: {1}=>{2} [START: {3:.3f}s | DUR: {4:.3f}s]'.format(__name__, self.state, self.next_state,
                                                                          self._current.start_time
                                                                          - self._runtime.get_time('start'),
                                                                          self.current.duration)


class State(object):
    """
    Handle information and methods associated with a state of the state machine

    Usage:
    state = State('my_state', duration=2.0)
    state.start()
    while state.status:
       if not state.status:
            state.stop()
            break

    """
    def __init__(self, name, duration=False):
        """
        State constructor
        :param name:
        :param duration:
        """
        self._name = name  # Name of the state
        self._status = False  # Status: False if the state has finished
        self._max_duration = duration  # Maximum duration of the state (can be False (no limit), 0.0, or float > 0.0)
        self._timer = None  # State timer
        self._start_time = None  # State starting time
        self._end_time = None  # State ending time
        self._duration = 0.0  # State duration
        self._running = False  # Has the state started already
        self.__singleshot = SingleShot()

    @property
    def running(self):
        return self._running

    @property
    def status(self):
        """
        Return status of current state: True if it is time to move on
        :return:
        """
        if self._running and self._max_duration is not False:
            self._status = self._timer.get_time('elapsed') >= self._max_duration
        else:
            self._status = False
        return self._status

    def singleshot(self, name, target=None, **kwargs):
        """
        Handles single shot events specific to this state
        :param name:
        :param target:
        :param kwargs:
        :return:
        """
        if target is not None:
            return self.__singleshot.run(name, target=target, **kwargs)
        else:
            return self.__singleshot[name]

    @property
    def duration(self):
        self._duration = self._timer.get_time('elapsed')
        return self._duration

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    def start(self):
        """
        Start state
        :return:
        """
        self._timer = Timer(max_duration=self._max_duration)
        self._timer.start()
        self._start_time = self._timer.get_time('start')
        self._running = True

    def stop(self):
        """
        End state
        :return:
        """
        # Stop and reset timer
        self._timer.stop()
        self._end_time = self._timer.get_time('stop')
        self._running = False


class SingleShot(object):
    """
    SingleShot events
    This class is a container for single shot events. It makes sure the event or target function is only executed once.

    Usage:
    singleshot = SingleShot()

    # in a conditional statement
    for i in range(5):
        if singleshot['name_of_event']:
            print('event is fired')

    This example should only print 'event is fired' once.

    # Same applies for calling functions
    def target_function(text):
        print(text)

    for i in range(5):
        singleshot.run('name_of_event', target=target_function, text='Hello, world!')

    This example will only execute target_function() once.

    Note that for target functions, the 'name' argument is optional. In this case, a "default" label will be
    used:

    singleshot(target=target_function, text='Hello, world!')  # Will print 'Hello, world!'
    singleshot(target=target_function, text='Goodbye, world!')  # Will do nothing because handled by "default"
    """

    def __init__(self):
        """
        SingleShot constructor
        """
        self.__events = dict()

    def __getitem__(self, item):
        """
        Return event status
        :param item: event's label
        :type item: str
        :return: event status (True if it has not been fired yet)
        """
        if item in self.__events:
            return False
        else:
            self.__events[item] = False
            return True

    def run(self, item='default', target=object, **kwargs):
        """
        Execute a target function only once
        :param item: event label
        :type item: str
        :param target: target function
        :type target: function
        :param kwargs: target function's arguments
        :type kwargs: dict
        :return: boolean
        :rtype: bool
        """
        if item not in self.__events:
            try:
                target(**kwargs)
                self.__events[item] = False
                return True
            except:
                raise Exception('Could not fire singleshot')
        else:
            return False


#######################################
# Example-related functions and classes
#######################################

def go_next():
    """
    Check if we should move to next state. For example, this function could listen to key press and return True if a
    certain key has been pressed.
    :rtype: bool
    """
    prob = 0.05  # Probability of moving to next state
    value = np.random.random()
    return value <= prob


def show(text):
    """
    Simple function that prints some text
    :param text:
    :return:
    """
    print(text)


from system.customlogger import CustomLogger
import logging
import threading


class TestMachine(object):
    """
    Test machine
    """

    def __init__(self):
        self.threads = None
        self.status = True
        self.timings = {
            "no_duration": False,
            "zero": 0.0,
            "duration": 2.0,
            "quit": 0.0
        }
        self.logger = CustomLogger('root', 'test.log')
        self.queues = {}
        self.state_machine = None

    def run(self):
        """
        Application main loop
        DO NOT MODIFY
        """
        self.state_machine = StateMachine(timings=self.timings, logger=self.logger)
        self.state_machine.state = 'no_duration'
        self.state_machine.next_state = 'duration'

        self.threads = threading.Thread(name='fast', target=self.fast_loop)
        self.threads.start()

        self.graphics_loop()
        self.threads.join()

    def quit(self):
        self.status = False
        self.threads.join()

    def graphics_loop(self):
        """
        Graphic state machine loop
        :return:
        """
        lapses = []
        while self.status:
            init_time = time.time()
            # Custom Graphics state
            self.graphics_state_machine()

            # Simulate screen flip
            time.sleep(0.016)

            # Update display
            stop_time = time.time() - init_time
            lapses.append(stop_time)

        mean_lapse = np.mean(lapses)
        self.logger.debug('Average lapse for GRAPHICS: {} ms'.format(mean_lapse * 1000))

    def fast_loop(self):
        """
        Fast state machine loop
        :return:
        """
        lapses = []
        start = time.time()
        while self.status:
            init_time = time.time()

            # Check state status
            if self.state_machine.change_state(force_move_on=go_next()):
                # Send events to devices that will be written into their data file
                self.logger.debug("Send message to devices")

            # Custom Fast states
            self.fast_state_machine()

            stop_time = time.time() - init_time
            lapses.append(stop_time)

            if time.time() - start > 5.0:
                self.logger.info('Time is up')
                self.status = False
                break

        mean_lapse = np.mean(lapses)
        self.logger.debug('Average lapse for FAST: {} ms'.format(mean_lapse * 1000))

    def fast_state_machine(self):

        if self.state_machine.state == 'no_duration':
            self.state_machine.next_state = 'zero'
            if self.state_machine.singleshot('first'):
                self.logger.debug('No Duration 1st')
            if self.state_machine.singleshot('second'):
                self.logger.debug('No duration 2nd')
            if self.state_machine.singleshot('second'):
                self.logger.debug('This message should not be printed')

            # Fire target function only once
            self.state_machine.singleshot('third', target=show, text='Hello world')

            # If no label is specified, then "default" will be used
            if self.state_machine.singleshot():
                self.logger.debug('again')

            # This event will never be executed because it also uses "default" label (no label has been specified)
            if self.state_machine.singleshot():
                self.logger.debug('This message should not be printed')

        elif self.state_machine.state == 'zero':
            self.state_machine.next_state = 'duration'
            if self.state_machine.singleshot('zero'):
                self.logger.debug('Zero')

        elif self.state_machine.state == 'duration':
            self.state_machine.next_state = 'quit'
            if self.state_machine.singleshot('duration'):
                self.logger.debug('Duration')

        elif self.state_machine.state == 'quit':
            if self.state_machine.singleshot:
                self.logger.debug('Quit')
                self.status = False

    def graphics_state_machine(self):
        if self.state_machine.state == 'no_duration':
            self.state_machine.next_state = 'zero'
            if self.state_machine.singleshot('graphics_first'):
                self.logger.debug('No Duration 1st')
            if self.state_machine.singleshot('graphics_second'):
                self.logger.debug('No duration 2nd')
            if self.state_machine.singleshot('graphics_second'):
                self.logger.debug('This message should not be printed')

            # Fire target function only once
            self.state_machine.singleshot('third', target=show, text='Hello world')

            # If no label is specified, then "default" will be used
            if self.state_machine.singleshot():
                self.logger.debug('again')

            # This event will never be executed because it also uses "default" label (no label has been specified)
            if self.state_machine.singleshot():
                self.logger.debug('This message should not be printed')

        elif self.state_machine.state == 'zero':
            self.state_machine.next_state = 'duration'
            if self.state_machine.singleshot('graphics_zero'):
                self.logger.debug('Zero')

        elif self.state_machine.state == 'duration':
            self.state_machine.next_state = 'quit'
            if self.state_machine.singleshot('graphics_duration'):
                self.logger.debug('Duration')

if __name__ == "__main__":
    import numpy as np

    Machine = TestMachine()
    Machine.run()






