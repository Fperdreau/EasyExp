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

__version__ = "1.0.0"


class Trigger(object):
    """
    Trigger class
    This is a container for triggers. It behaves like a dictionary but makes sure that triggers are retrieved in order.

    Usage:
    trigger = Trigger()  # Instantiate Trigger class
    trigger.add('first')  # Add trigger
    trigger.add('second')
    trigger.add('third')
    trigger['first'] = True  # Set new value to trigger

    for item, value in trigger.iteritems():
        print(item, value)

    This should print:
        ('first', True)
        ('second', False)
        ('third', False)
    """

    def __init__(self):
        """
        Trigger constructor
        """
        self.__triggers = dict()
        self.__ids = dict()
        self.__curr_id = 0

    def add(self, name, value=False):
        """
        Add trigger to collection
        :param name: trigger name
        :type name: str
        :param value: trigger value (False is default)
        :type value: bool
        :return:
        """
        if name not in self.__triggers:
            self.__triggers.update({name: value})
            self.__set_id(name)

    def __getitem__(self, item):
        """
        Get trigger value
        This allows trigger to be accessed by calling: Trigger['trigger_name']
        :param item: trigger name
        :type item: str
        :return:
        """
        if item in self.__triggers:
            return self.__triggers[item]

    def __setitem__(self, key, value):
        """
        Set new value to trigger
        This allows setting new value to trigger by calling Trigger['trigger_name'] = new_value
        :param key: trigger name
        :type key: str
        :param value: new value
        :return:
        """
        if key in self.__triggers:
            self.__triggers[key] = value

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
            yield item, self.__triggers[item]

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
        for item in self.__triggers:
            self.__triggers[item] = False

    def remove(self, item):
        """
        Remove trigger from collection
        :param item: trigger name
        :type item: str
        :return:
        """
        if item in self.__triggers:
            del self.__triggers[item]
            self.__del_id(item)


if __name__ == "__main__":

    trigger = Trigger()  # Instantiate Trigger class
    trigger.add('first')  # Add trigger
    trigger.add('second')
    trigger.add('third')
    trigger['first'] = True  # Set new value to trigger

    for item, value in trigger.iteritems():
        print(item, value)

    # This should print:
    # ('first', True)
    # ('second', False)
    # ('third', False)
