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
import numpy as np


class StateMachine(object):
    """
    State class
    Implement state of state machine
    """

    def __init__(self, timings=dict, queue=None, configurer=None):
        """
        State constructor
        Parameters
        ----------
        :param timings: dictionary specifying states timings
        :type timings: dict
        :param configurer: logger configurer
        :type queue: Multiprocessing queue
        """
        self.durations = timings

        self._state = None
        self._current = None
        self._next_state = None

        self.logger = None
        self.get_logger(queue, configurer)

        self._runtime = Timer()
        self._runtime.start()

    def get_logger(self, queue, configurer):
        """
        Get application logger. Logger runs in an independent process?
        :param queue:
        :param configurer:
        :return:
        """
        configurer(queue)
        self.logger = logging.getLogger('root')

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
        self._current = State(self.state, duration=self.durations[self.state])
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

        # Check inputs and timers
        # move_on = force_move_on or (self._current.status and self._current.running)

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


def go_next():
    """
    Check if we should move to next state. For example, this function could listen to key press and return True if a
    certain key has been pressed.
    :rtype: bool
    """
    prob = 0.05  # Probability of moving to next state
    value = np.random.random()
    time.sleep(0.01)
    return value <= prob


def show(text):
    """
    Simple function that prints some text
    :param text:
    :return:
    """
    print(text)


from system import mplogger as l
# import multiprocessing as mp
import multiprocess as mp
import logging


class TestMachine(object):
    def __init__(self, my_logger=None):
        self.threads = None
        self.status = True
        self.timings = {
            "no_duration": False,
            "zero": 0.0,
            "duration": 2.0,
            "quit": 0.0
        }
        self.logger = my_logger
        self.queues = {}
        self.state_machine = None

    def listener_process(self, queue, configurer):
        configurer()
        while True:
            try:
                record = queue.get()
                if record is None:  # We send this as a sentinel to tell the listener to quit.
                    break
                logger = logging.getLogger(record.name)
                logger.handle(record)  # No level or filter logic applied - just do it!
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                import sys, traceback
                print >> sys.stderr, 'Whoops! Problem:'
                traceback.print_exc(file=sys.stderr)

    def run(self):
        """
        Application main loop
        DO NOT MODIFY
        """
        manager = mp.Manager()
        self.queues = manager.Queue(-1)
        # self.queue = mp.Queue(-1)

        # Start listener
        listener = mp.Process(target=l.listener_process, args=(self.queues, l.listener_configurer))
        listener.start()

        self.state_machine = StateMachine(timings=self.timings, queue=self.queues, configurer=l.worker_configurer)
        self.state_machine.state = 'no_duration'
        self.state_machine.next_state = 'duration'

        worker = mp.Process(target=self.fast_loop, args=(self.queues, l.worker_configurer))
        worker.start()

        self.graphics_loop(queues=self.queues, configurer=l.worker_configurer)
        worker.join()

        self.queues.put_nowait(None)
        self.queues.join()

        listener.join()

    def quit(self):
        self.status = False
        self.threads.join()
        self.queue.put_nowait(None)
        self.listener.join()

    def graphics_loop(self, queues, configurer):
        """
        Graphic state machine loop
        :return:
        """
        configurer(queues)
        name = mp.current_process().name
        print('Graphics Worker started: %s' % name)
        lapses = []
        logger = logging.getLogger('root')

        while self.status:
            self.status = queues.get(False)


            init_time = time.time()
            # Custom Graphics state
            self.graphics_state_machine(logger)

            # Update display
            stop_time = time.time() - init_time
            lapses.append(stop_time)

        mean_lapse = np.mean(lapses)
        logger.debug('Average lapse for GRAPHICS: {} ms'.format(mean_lapse * 1000))
        logger.info('Worker finished: {}'.format(name))

    def fast_loop(self, queues, configurer):
        """
        Fast state machine loop
        :return:
        """
        name = mp.current_process().name
        print('Fast Worker started: %s' % name)
        h = l.QueueHandler(queues)  # Just the one handler needed
        logger = logging.getLogger()
        logger.addHandler(h)
        logger.setLevel(logging.DEBUG)  # send all messages, for demo; no other level or filter logic applied.
        lapses = []
        start = time.time()
        while self.status:
            init_time = time.time()

            # Check state status
            #if self.state_machine.change_state(force_move_on=go_next()):
                # Send events to devices that will be written into their data file
            #    logger.debug("Send message to devices")

            # Custom Fast states
            #self.fast_state_machine(logger)

            stop_time = time.time() - init_time
            lapses.append(stop_time)

            if time.time() - start > 5.0:
                logger.info('Time is up')
                self.status = False
                break

        mean_lapse = np.mean(lapses)
        logger.debug('Average lapse for FAST: {} ms'.format(mean_lapse * 1000))
        logger.info('Worker finished: {}'.format(name))

    def fast_state_machine(self, logger):

        if self.state_machine.state == 'no_duration':
            self.state_machine.next_state = 'zero'
            if self.state_machine.singleshot('first'):
                logger.debug('No Duration 1st')
            if self.state_machine.singleshot('second'):
                logger.debug('No duration 2nd')
            if self.state_machine.singleshot('second'):
                logger.debug('This message should not be printed')

            # Fire target function only once
            self.state_machine.singleshot('third', target=show, text='Hello world')

            # If no label is specified, then "default" will be used
            if self.state_machine.singleshot():
                logger.debug('again')

            # This event will never be executed because it also uses "default" label (no label has been specified)
            if self.state_machine.singleshot():
                logging.debug('again, again')

        elif self.state_machine.state == 'zero':
            self.state_machine.next_state = 'duration'
            if self.state_machine.singleshot('zero'):
                logger.debug('Zero')

        elif self.state_machine.state == 'duration':
            self.state_machine.next_state = 'quit'
            if self.state_machine.singleshot('duration'):
                logger.debug('Duration')

        elif self.state_machine.state == 'quit':
            if self.state_machine.singleshot:
                logger.debug('Quit')
                self.status = False

    def graphics_state_machine(self, logger):
        if self.state_machine.state == 'no_duration':
            self.state_machine.next_state = 'zero'
            if self.state_machine.singleshot('graphics_first'):
                logger.debug('No Duration 1st')
            if self.state_machine.singleshot('graphics_second'):
                logger.debug('No duration 2nd')
            if self.state_machine.singleshot('graphics_second'):
                logger.debug('No duration 3nd')

            # Fire target function only once
            self.state_machine.singleshot('third', target=show, text='Hello world')

            # If no label is specified, then "default" will be used
            if self.state_machine.singleshot('graphics_again'):
                logger.debug('again')

            # This event will never be executed because it also uses "default" label (no label has been specified)
            if self.state_machine.singleshot():
                logger.debug('again, again')

        elif self.state_machine.state == 'zero':
            self.state_machine.next_state = 'duration'
            if self.state_machine.singleshot('graphics_zero'):
                logger.debug('Zero')

        elif self.state_machine.state == 'duration':
            self.state_machine.next_state = 'quit'
            if self.state_machine.singleshot('graphics_duration'):
                logger.debug('Duration')


# States duration (in seconds)
# if duration is False, then the state machine will stay within the same state until told otherwise
# if duration is 0.0, then the state machine will immediately move to the next state
# if duration is float > 0.0, then the state machine will stay in the same state for the given duration

durations = {
    "no_duration": False,
    "zero": 0.0,
    "duration": 2.0,
    "quit": 0.0
}


if __name__ == "__main__":
    import numpy as np

    Machine = TestMachine()
    Machine.run()






