#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

__version__ = "1.1.0"


class Stimuli(object):
    """
    Stimuli class
    This is a container for stimuli. It behaves like a dictionary but makes sure that stimuli are retrieved in order.

    Usage:
    stimuli = Stimuli()  # Instantiate Stimuli class
    stimuli.add('stimulus_name', stimulus_instance)  # Add stimulus

    stimuli['first'].on()  # Set stimulus' status to True
    stimuli['first'].off()  # Set stimulus' status to False

    stimuli.reset()  # Set all stimuli's status to False
    stimuli.remove_all()  # Delete all stimuli's instance

    Each stimuli instance and its properties/methods can be accessed by calling:
    stimuli['stimulus_name'].__property_name
    or
    stimuli['stimulus_name'].__method_name()

    for item, value in stimuli.iteritems():
        print(item)

    This should print:
        ('first', True)
        ('second', False)
        ('third', False)
    """

    def __init__(self):
        """
        Trigger constructor
        """
        self.__container = dict()
        self.__ids = dict()
        self.__curr_id = 0

    def add(self, name, instance):
        """
        Add trigger to collection
        :param name: trigger name
        :type name: str
        :param instance: stimulus instance
        :type instance: object
        :return:
        """
        if name not in self.__container:
            self.__container.update({name: Stimulus(instance)})
            self.__set_id(name)
        else:
            self.__container[name] = Stimulus(instance)

    def __getitem__(self, name):
        """
        Get trigger value
        This allows trigger to be accessed by calling: Trigger['trigger_name']
        :param name: trigger name
        :type name: str
        :return:
        """
        if name in self.__container:
            return self.__container[name]

    def __setitem__(self, key, instance):
        """
        Set new value to trigger
        This allows setting new value to trigger by calling Trigger['trigger_name'] = new_value
        :param key: trigger name
        :type key: str
        :param instance: new value
        :type instance: object
        :return:
        """
        if key in self.__container:
            self.__container[key] = Stimulus(instance)

    def __iter__(self):
        """
        Iteration method: returns triggers value in order
        :return:
        """
        for item_id, item in sorted(self.__ids.iteritems()):
            yield item

    def iteritems(self):
        """
        Iteration method: returns triggers name and value in order
        :return:
        """
        for item_id, item in sorted(self.__ids.iteritems()):
            yield item, self.__container[item]

    def __set_id(self, item):
        """
        Give an id to new trigger
        :param item: trigger name
        :type item: str
        :return:
        """
        if str(self.__curr_id) not in self.__ids:
            self.__ids.update({str(self.__curr_id): item})
            self.__curr_id += 1

    def __get_id(self, item):
        """
        Get trigger's id
        :param item: trigger name
        :type item: str
        :return:
        """
        for item_id, it in self.__ids.iteritems():
            if it == item:
                return item_id
        return None

    def __del_id(self, item):
        """
        Delete trigger'id
        :param item: trigger name
        :type item: str
        :return:
        """
        item_id = self.__get_id(item)
        if item_id is not None and item_id in self.__ids:
            del self.__ids[item_id]

    def __get_item(self, item_id):
        """
        Get trigger's name from id
        :param item_id: trigger id
        :type item_id: str or int
        :return:
        """
        if str(item_id) in self.__ids:
            return self.__ids[str(item_id)]

    def reset(self):
        """
        Set all triggers to False
        :return:
        """
        for item in self.__container:
            self.__container[item].off()

    def remove(self, item):
        """
        Remove stimuli from collection
        :param item: trigger name
        :type item: str
        :return:
        """
        if item in self.__container:
            del self.__container[item]
            self.__del_id(item)

    def remove_all(self):
        """
        Delete all stimuli
        :return: void
        """
        self.__container = dict()

    def get_positions(self):
        """
        Get all stimuli positions
        :return: dictionary providing each stimulus position (dict('stimulus_name': [float, float, float])
        :rtype: dict
        """
        positions = dict()
        for stimulus_name, obj in self.iteritems():
            positions[stimulus_name] = obj.pos
        return positions


class Stimulus(object):
    """
    Stimulus class
    Hold stimulus instance and extends its attributes/methods with on() and off() methods, and status property
    """

    def __init__(self, obj):
        self.__instance = obj
        self.__status = False

    def on(self):
        self.__status = True

    def off(self):
        self.__status = False

    @property
    def status(self):
        return self.__status

    def __getattr__(self, name):
        """
        Magic method
        :param name:
        :return:
        """
        try:
            return getattr(self.__instance, name)
        except AttributeError:
            raise AttributeError(
                "'%s' object has no attribute '%s'" % (type(self).__name__, name))


if __name__ == "__main__":
    from psychopy import visual
    import time
    import pygame

    # Window
    win = visual.Window(
        size=(1680, 1050),
        monitor='TestMonitor',
        color=(-1, -1, -1),
        pos=(0, 0),
        units='pix',
        winType='pygame',
        fullscr=True)

    stimuli = Stimuli()  # Instantiate Trigger class
    stimuli.add(
        'red_circle',
        visual.Circle(win, radius=20.0, pos=(0.0, 0.0), lineWidth=1, lineColor=(1.0, 0.0, 0.0),
                      fillColor=(1.0, 0.0, 0.0), units='pix')
    )

    stimuli.add(
        'green_circle',
        visual.Circle(win, radius=20.0, pos=(0.0, 0.0), lineWidth=1, lineColor=(0.0, 1.0, 0.0),
                      fillColor=(0.0, 1.0, 0.0), units='pix')
    )

    stimuli.add(
        'blue_circle',
        visual.Circle(win, radius=20.0, pos=(0.0, 0.0), lineWidth=1, lineColor=(0.0, 0.0, 1.0),
                      fillColor=(0.0, 0.0, 1.0), units='pix')
    )  # Add stimulus

    # Start trial
    # Here, we simply draw a black dot at the current gaze location. YAY, our first gaze-contingent experiment!
    trialDuration = 5
    initTime = time.time()
    while time.time() < initTime + trialDuration:
        time_from_start = time.time() - initTime

        stimuli.reset()
        if time_from_start < 1.0:
            stimuli['red_circle'].on()
        elif time_from_start < 2.0:
            stimuli['green_circle'].on()
        elif time_from_start < 3.0:
            stimuli['blue_circle'].on()

        for name, stimulus in stimuli.iteritems():
            if stimulus.status:
                stimulus.draw()

        win.flip()

        pygame.event.pump()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            break

    # Test order
    for name, stimulus in stimuli.iteritems():
        print(name)

    # This should print:
    # 'red_circle'
    # 'green_circle'
    # 'blue_circle'
