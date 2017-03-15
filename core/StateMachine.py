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

import version


class StateMachine(object):
    """
    StateMachine class
    Handles transition between states

    API:
    - StateMachine.next_state = "next_state": set next state
    - StateMachine.state = "state_name": set current state
    - StateMachine.start(): start current state
    - StateMachine.stop(): stop current state
    - StateMachine.change_state(force_move_on=False): move to next state if conditions are reached.
    - StateMachine.move_on(): force transition to next state
    """

    def __init__(self, timings=None, logger=None):
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
        :type logger: logging.logger|CustomLogger
        """
        self.__durations = timings if timings is not None else dict()
        self.__logger = logger

        self.__state = None
        self.__current = None
        self.__next_state = None

        self.__runtime = Timer()
        self.__runtime.start()

        self.__counter = 0
        self._syncer = None

        self.__move_on_requested = False

    @property
    def logger(self):
        """
        Get logger
        :return:
        """
        return self.__logger if self.__logger is not None else logging.getLogger(version.__app_name__)

    @logger.setter
    def logger(self, logger):
        """
        Set logger
        :param logger: logger
        :return:
        """
        self.__logger = logger

    @property
    def current(self):
        """
        Get current state
        :return:
        """
        return self.__current

    @property
    def state(self):
        """
        Get current state
        :return:
        """
        return self.__state

    @state.setter
    def state(self, new_state):
        """
        Set current state
        :param new_state: new state
        :type new_state: str
        :return:
        """
        self.__state = new_state

    @property
    def next_state(self):
        """
        Get next state
        :return:
        """
        return self.__next_state

    @next_state.setter
    def next_state(self, next_state):
        """
        Set next state
        :param next_state: next state
        :type next_state: str
        :return:
        """
        self.__next_state = next_state

    @property
    def durations(self):
        """
        Get states durations
        :return:
        """
        return self.__durations

    @durations.setter
    def durations(self, timings):
        """
        Update durations or set new durations
        :param timings:
        :type timings: dict
        :return:
        """
        self.__durations.update(timings)

    def add_syncer(self, nb_threads, lock=None):
        """
        Add Syncer instance
        :param lock:
        :param nb_threads:
        :return:
        """
        if self._syncer is None:
            self._syncer = Syncer(nb_thread=nb_threads, lock=lock)

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
        :rtype: bool
        """
        # If we enter a new state
        self.__current = State(self.state, duration=self.__durations[self.state])
        self.__current.start()
        msg = "[{0}] '{1}' state begins [t={2:1.3f}]".format(__name__, self.state.upper(),
                                                             self.current.start_time - self.__runtime.get_time('start'))
        self.__logger.info(msg)

        self.__move_on_requested = False

    def stop(self):
        """
        Stop current state
        :return:
        """
        if self.current is not None:
            # Stop current state
            self.current.stop()
            self.__logger.info(self)

            # Reset state watcher
            self.__reset_syncer()

            # Set new state
            self.state = self.next_state

            # Unset current state
            self.__current = None

    def __reset_syncer(self):
        """
        Reset state watcher
        :return: void
        """
        if self._syncer is not None:
            # self._syncer.get(self.state)
            self._syncer.reset()

    def __is_state_completed(self):
        """
        Check if current state has been executed by every running threads
        :return:
        """
        return self._syncer.completed(self.state) if self._syncer is not None else True

    def change_state(self):
        """
        This function handles transition between states
        :rtype: bool
        """
        if self.current is None:
            # If we enter a new state
            self.start()
            return True

        # If we transition to the next state
        if self.__is_state_completed() and (
                    (self.durations[self.state] is False and self.__move_on_requested)
                or (self.durations[self.state] is not False and self.current.status and self.current.running)
        ):

            # Stop current state
            self.stop()
            return False
        else:
            return False

    def jump(self):
        """
        Move directly to next state
        :return: bool
        """
        if self.current is not None:
            # If we enter a new state
            self.stop()
            return True
        return False

    def request_move_on(self):
        """
        Request transition to next state. This only has an effect if the current state has no maximum duration defined.
        :return: void
        """
        if not self.__move_on_requested:
            self.logger.info('[{}] STATE: {} - Move on requested'.format(__name__, self.state))
            self.__move_on_requested = True

    def __str__(self):
        """
        Print State information
        :return:
        """
        return "[{0}]: '{1}' state ends [DUR: {3:.3f}s | NEXT: {4}]".format(
            __name__, self.state.upper(), self.__current.start_time - self.__runtime.get_time('start'),
            self.current.duration, self.next_state)


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
        self.__name = name  # Name of the state
        self.__status = False  # Status: False if the state has finished
        self.__max_duration = duration  # Maximum duration of the state (can be False (no limit), 0.0, or float > 0.0)
        self.__timer = None  # State timer
        self.__start_time = None  # State starting time
        self.__end_time = None  # State ending time
        self.__duration = 0.0  # State duration
        self.__running = False  # Has the state started already
        self.__executed = False
        self.__singleshot = SingleShot()

    @property
    def running(self):
        return self.__running

    @property
    def executed(self):
        """
        Set state as executed
        :return:
        """
        return self.__executed

    def execute(self):
        """
        Set state as executed
        :return:
        """
        if not self.__executed:
            self.__executed = True

    @property
    def status(self):
        """
        Return status of current state: True if it is time to move on
        :return:
        """
        if self.__running and self.__max_duration is not False:
            self.__status = self.__timer.get_time('elapsed') >= self.__max_duration
        else:
            self.__status = False
        return self.__status

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
        self.__duration = self.__timer.get_time('elapsed')
        return self.__duration

    @property
    def start_time(self):
        return self.__start_time

    @property
    def end_time(self):
        return self.__end_time

    def start(self):
        """
        Start state
        :return:
        """
        self.__timer = Timer(max_duration=self.__max_duration)
        self.__timer.start()
        self.__start_time = self.__timer.get_time('start')
        self.__running = True

    def stop(self):
        """
        End state
        :return:
        """
        # Stop and reset timer
        self.__timer.stop()
        self.__end_time = self.__timer.get_time('stop')
        self.__running = False


class Syncer(object):
    """
    Syncer class
    """

    def __init__(self, nb_thread=1, lock=None):
        """
        Syncer's constructor
        :param nb_thread:
        """
        self.__child = {}
        self.__nb_thread = nb_thread
        self.__lock = threading.RLock() if lock is None else lock

    def count(self, thread, state):
        """
        Append thread to the list of threads having executed the current state
        :param thread:
        :param state:
        :return: void
        """
        with self.__lock:
            self.__add_state(state)

            if state in self.__child and thread not in self.__child[state]:
                self.__child[state].append(thread)

    def __add_state(self, state):
        """
        Add state to watched list
        :param state:
        :return: void
        """
        if state not in self.__child:
            self.__child.update({state: []})

    def completed(self, state):
        """
        Check all threads threads have fully executed the current state
        :param state:
        :return: Has the current state been executed by all running threads?
        :rtype: bool
        """
        with self.__lock:
            if state in self.__child:
                return len(self.__child[state]) == self.__nb_thread
            else:
                return False

    def get(self, state):
        if state in self.__child:
            print(self.__child[state])

    def reset(self):
        """
        Reset watched list
        :return: void
        """
        self.__child = {}


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
    prob = 0.000005  # Probability of moving to next state
    value = np.random.random()
    return value <= prob


def show(text):
    """
    Simple function that prints some text
    :param text:
    :return:
    """
    print('{}\n'.format(text))


from system.customlogger import CustomLogger
import logging
import threading
from threading import RLock


class TestMachine(StateMachine):
    """
    Test machine
    """

    def __init__(self):
        super(TestMachine, self).__init__(timings={
            "no_duration": False,
            "zero": 0.0,
            "duration": 2.0,
            "quit": 0.0
        })
        self.threads = None
        self.status = True
        self.state = 'no_duration'
        self.next_state = 'duration'
        self.logger = CustomLogger('root', 'test.log')
        self.queues = {}
        self.lock = RLock()
        self.add_syncer(2, self.lock)

    def run(self):
        """
        Application main loop
        DO NOT MODIFY
        """
        self.threads = threading.Thread(name='fast', target=self.fast_loop)
        self.threads.start()

        self.graphics_loop()
        self.quit()

    def quit(self):
        """
        Quit Test machine and stop all threads
        :return:
        """
        self.status = False
        self.threads.join()

    def graphics_loop(self):
        """
        Graphic state machine loop
        :return:
        """
        counter = 0
        init_time = time.time()
        while self.status:
            # Custom Graphics state
            self.graphics_state_machine()

            # Add state to watcher
            self._syncer.count('graphics', self.state)

            # Simulate screen flip
            time.sleep(0.016)

            # Increment loop counter
            counter += 1

        # Compute average looping time
        lapses = (time.time() - init_time) / float(counter)
        self.logger.debug('Average lapse for GRAPHICS: {} ms'.format(lapses * 1000))

    def fast_loop(self):
        """
        Fast state machine loop
        :return:
        """
        counter = 0
        init_time = time.time()
        while self.status:

            if go_next():
                self.request_move_on()

            # Check state status
            if self.change_state():
                # Send events to devices that will be written into their data file
                self.logger.debug("Send message to devices: {}".format(self.state))

            # Custom Fast states
            self.fast_state_machine()

            self._syncer.count('fast', self.state)

            # Increment loop counter
            counter += 1

            if time.time() - init_time > 5.0:
                self.logger.info('Time is up')
                self.status = False
                break

        # Compute average looping time
        lapses = (time.time() - init_time) / float(counter)
        self.logger.debug('Average lapse for FAST: {} ms'.format(lapses * 1000))

    def fast_state_machine(self):

        if self.state == 'no_duration':
            self.next_state = 'zero'
            counter = 0

            if self.singleshot('first'):
                counter += 1
                self.logger.debug('Fast: No Duration 1st')
            if self.singleshot('second'):
                counter += 1
                self.logger.debug('Fast: No duration 2nd')
            if self.singleshot('second'):
                counter += 1
                self.logger.debug('Fast: This message should not be printed')

            # Fire target function only once
            self.singleshot('third', target=show, text='Fast: Hello world')

            # If no label is specified, then "default" will be used
            if self.singleshot():
                counter += 1
                self.logger.debug('Fast: again')

            # This event will never be executed because it also uses "default" label (no label has been specified)
            if self.singleshot():
                counter += 1
                self.logger.debug('Fast: This message should not be printed')

            if self.singleshot('assert'):
                assert counter == 3

        elif self.state == 'zero':
            self.next_state = 'duration'
            if self.singleshot('zero'):
                self.logger.debug('Fast: Zero')

        elif self.state == 'duration':
            self.next_state = 'quit'
            if self.singleshot('duration'):
                self.logger.debug('Fast: Duration')

        elif self.state == 'quit':
            if self.singleshot:
                self.logger.debug('Fast: Quit')
                self.status = False

    def graphics_state_machine(self):
        if self.state == 'no_duration':
            self.next_state = 'zero'
            if self.singleshot('graphics_first'):
                self.logger.debug('Graphics: No Duration 1st')
            if self.singleshot('graphics_second'):
                self.logger.debug('Graphics: No duration 2nd')
            if self.singleshot('graphics_second'):
                self.logger.debug('Graphics: This message should not be printed')

            # Fire target function only once
            self.singleshot('third', target=show, text='Graphics: Hello world')

        elif self.state == 'zero':
            self.next_state = 'duration'
            if self.singleshot('graphics_zero'):
                self.logger.debug('Graphics: Zero')

        elif self.state == 'duration':
            self.next_state = 'quit'
            if self.singleshot('graphics_duration'):
                self.logger.debug('Graphics: Duration')

if __name__ == "__main__":
    import numpy as np

    Machine = TestMachine()
    try:
        Machine.run()
    except AssertionError as e:
        Machine.logger.error(e)
        Machine.quit()
        raise e







