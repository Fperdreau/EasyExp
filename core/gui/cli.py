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

__author__ = "Florian Perdreau"
__copyright__ = "Copyright 2015, Florian Perdreau"
__license__ = "GPL"
__version__ = '1.1'
__maintainer__ = "Florian Perdreau"
__email__ = "f.perdreau@donders.ru.nl"


class BaseCli(object):
    """
    Base class for command line interfaces handling user inputs
    Child classes must implement a populate method, otherwise an exception will be raised
    """

    def __init__(self):
        """
        BaseCli constructor
        :return:
        """
        self.entries = dict()
        self.types = list()
        self.out = dict()
        self.title = None

    def display_title(self):
        """
        Display form title
        :return: void
        """
        print('..:: {} ::..'.format(self.title))

    def initUI(self):
        """
        Init application GUI
        :return void
        """
        # Render title
        self.display_title()

        # Render form
        self.populate()

    def populate(self):
        """
        Populates form
        :return:
        """
        raise NotImplementedError("Should have implemented this")

    @staticmethod
    def process_section(section):
        """
        Ask user if we should show section's options
        :param section:
        :return:
        """
        return BaseCli.waiting_for_response('{} section: do you want to proceed [yes, no (selected)]? '.format(section),
                                            ['yes', 'no'], default='no')

    @staticmethod
    def waiting_for_response(msg, options=None, default=None):
        """
        Prompt the user with requested input until he gives an answer present amongst the possible options
        :param msg: Message to display
        :type msg: str
        :param options: List of possible answers
        :type options: list
        :return: User's answer
        :param default: default value. If default is set and the user does not enter any response, then this function
        will return this default value.
        :rtype: str
        """
        out = None
        lowered_options = [i.lower() for i in options] if options is not None else None
        while True:
            out = raw_input(msg).lower()
            if (default is not None and out == '') or (options is None and out != '') or (out in lowered_options):
                if default is not None and out == '':
                    out = str(default)  # Convert to string to make sure this method always returns the same type
                break
            else:
                logging.warning('Unexpected response. Options are {}'.format(', '.join(options)))
        return out

    @staticmethod
    def input(label, value=''):
        """
        Renders text input
        :param label:
        :param value:
        :return:
        """
        out = raw_input('{} [default: {}]:'.format(label, value))
        return out if out != '' else value

    @staticmethod
    def select(label, value, options):
        """
        Ask user to select one value amongst a list of options
        :param label: input label
        :param value: current setting
        :param options: options
        :return:
        """
        string = ['{} (selected)'.format(i) if i == value else str(i) for i in options]
        stringified = [str(i) for i in options]
        # If default value exists, then add possibility to skip this setting without giving an answer
        if value != '':
            stringified.append('')
        msg = '{} [Options: {}]:'.format(label, ', '.join(string))
        out = BaseCli.waiting_for_response(msg, stringified)
        return out if out != '' else value

    @staticmethod
    def checkbox(label, value, options):
        """
        Ask user to select one value amongst a list of options
        :param label: input label
        :param value: current setting
        :param options: options
        :return:
        """
        return BaseCli.select(label, value, options)

    def get_type(self, value):
        """
        Get value type
        :param value:
        :return: input type
        :rtype: str
        """
        #  Guess the entry type
        if type(value) is not str and isinstance(value, set):
            # If array, then create a selection list
            self.types.append('list')
            return 'list'
        elif type(value) is not str and isinstance(value, bool):
            # if boolean, then create radio buttons
            self.types.append('bool')
            return 'bool'
        elif isinstance(value, int):
            self.types.append('int')
            return 'int'
        elif isinstance(value, float):
            self.types.append('float')
            return 'float'
        else:
            self.types.append('str')
            return 'str'

    def fetch(self):
        """
        Parse inputs
        :return:
        """
        raise NotImplementedError("Should have implemented this")

    def parse_field(self, entry):
        """
        Parse field and convert input type
        :param entry:
        :return: field's input
        """
        var_type = entry[2]  # input type
        out = entry[1]  # input value
        if var_type == 'bool':
            # Convert to boolean if not boolean
            if isinstance(out, str):
                out = out.lower() == "true"
            elif isinstance(out, int):
                out = out == 1
        elif var_type == 'int':
            out = int(out)
        elif var_type == 'float':
            out = float(out)
        elif var_type == 'list':
            list = out.split(',')
            out = list()
            for item in list:
                try:
                    value = float(item)
                except TypeError:
                    value = str(item)
                out.append(value)
        else:
            out = str(out)
        print(out)
        return out


class SimpleCli(BaseCli):
    """
    This class renders a CLI form from data provided by a JSON settings file. It handles methods to read and parse the
    settings file, as well as inputs given by the user, and update the settings file accordingly.
    The JSON file should be formatted as follow:

    # Data format
    Whether data are stored in a variable or in a JSON file, they should respect the following format:
    {
        "simple_input": "r",
        "list of strings": ['option1', 'option2', 'option3'],
        "list of int or float": ['option1', 'option2', 'option3'],
        "bool_select": False,
        "Int_option": 0
    }

    @usage
    ```
        # Path to settings file
        path_to_settings_file = "simple_settings.json"

        # Read data from settings file
        with open(path_to_settings_file) as data_file:
            data = json.load(data_file)

        # Render GUI form
        info = SimpleCli(data)

        # Update settings file with inputs provided by the user (inputs are stored in info.out)
        with open(path_to_settings_file, 'w', 0) as fid:
            json.dump(info.out, fid, indent=4)
    ```
    """

    def __init__(self, input_data, title="DialogUI", mandatory=True):
        """
        DialogGUI constructor
        :param dict input_data:
        :param str title:
        :param mandatory: if set to False, then ask participant if we must show section's settings or if we must skip
         to the next session. If True, then the user would have to go through every setting.
        :type mandatory: bool

        :return:
        """
        super(SimpleCli, self).__init__()

        self.data = input_data  # Input
        self.out = input_data  # Output
        self.title = title
        self.mandatory = mandatory
        self.entries = {}
        self.types = []

        self.initUI()
        self.fetch()

    def populate(self):
        """
        Populates form
        :return: void
        """
        for field_name, value in self.data.iteritems():
            # Guess the entry type
            var_type = self.get_type(value)

            # Convert list to comma separated string
            if var_type == 'list':
                value = ','.join(str(e) for e in value)

            # Build input
            if var_type == 'bool':
                out = self.checkbox(field_name, value, [True, False])
            else:
                out = self.input(field_name, value)

            if field_name in self.entries:
                self.entries[field_name] = (field_name, out, var_type)
            else:
                self.entries.update({
                    field_name: (field_name, out, var_type)
                })

    def fetch(self):
        """
        Fetch inputs
        :return:
        """
        i = 0
        for input_name, entry in self.entries.iteritems():
            out = self.parse_field(entry)
            self.out[input_name] = out
            i += 1


class NestedCli(BaseCli):
    """
    This class renders a GUI form from data provided by a JSON settings file. It handles methods to read and parse the
    settings file, as well as inputs given by the user, and update the settings file accordingly.
    The JSON file should be formatted as follow:
    ```
        {
            "section_name": {
                "input_name": {
                    "label": "input_label",
                    "type": "input_type",
                    "value": input_value,
                    "options": list_of_possible_inputs
                }
            }
        }

        example:
        {
            "Display": {
                "distance": {
                    "label": "Distance",
                    "type": "text",
                    "value": 1470.0
                },
                "fullscreen": {
                    "label": "Full screen",
                    "type": "checkbox",
                    "options": [true, false],
                    "value": false
                }
            }
        }

    ```
    Input type can be: 'text', 'checkbox' or 'select'

    @usage
    ```
        # Path to settings file
        path_to_settings_file = "settings.json"

        # Read data from settings file
        with open(path_to_settings_file) as data_file:
            data = json.load(data_file)

        # Render GUI form
        info = DialogGUI(data)

        # Update settings file with inputs provided by the user (inputs are stored in info.out)
        with open(path_to_settings_file, 'w', 0) as fid:
            json.dump(info.out, fid, indent=4)
    ```
    """

    def __init__(self, input_data, title="DialogUI", mandatory=True):
        """
        DialogGUI constructor
        :param dict input_data:
        :param str title:
        :param mandatory: if set to False, then ask participant if we must show section's settings or if we must skip
         to the next session. If True, then the user would have to go through every setting.
        :type mandatory: bool

        :return:
        """

        super(NestedCli, self).__init__()

        self.data = input_data  # Input
        self.out = input_data  # Output
        self.title = title
        self.mandatory = mandatory
        self.entries = {}
        self.types = []

        self.initUI()
        self.fetch()

    def populate(self):
        """
        Populates form
        :return: void
        """
        for key, section in self.data.iteritems():
            if not self.mandatory:
                if self.process_section(key) == 'no':
                    continue

            for field_name, info in section.iteritems():
                label = info['label']
                value = info['value']
                input_type = info['type']

                # Guess the entry type
                var_type = self.get_type(value)

                # Convert list to comma separated string
                if var_type == 'list':
                    value = ','.join(str(e) for e in value)

                # Build input
                if input_type == 'text':
                    out = self.input(label, value=value)
                elif input_type == 'select':
                    out = self.select(label, value, info['options'])
                elif input_type == 'checkbox':
                    out = self.checkbox(label, value, info['options'])
                else:
                    raise Exception('"{}": unsupported field type'.format(input_type))

                if key in self.entries:
                    self.entries[key][field_name] = (field_name, out, var_type)
                else:
                    self.entries.update({
                        key: {field_name: (field_name, out, var_type)}
                    })

    def fetch(self):
        """
        Parse inputs
        :return:
        """
        i = 0
        for section, entry in self.entries.iteritems():
            for input_name, ent in entry.iteritems():
                out = self.parse_field(ent)
                self.out[section][input_name]['value'] = out
                i += 1


if __name__ == '__main__':
    import json
    from pprint import pprint

    # Example with Simple Cli
    pathtofile = "simple_settings.json"
    with open(pathtofile) as data_file:
        data = json.load(data_file)

    expinfo = SimpleCli(data, 'Select Experiment', False)
    pprint(expinfo.out)

    # Example with nested Cli
    pathtofile = "nested_settings.json"
    with open(pathtofile) as data_file:
        data = json.load(data_file)

    expinfo = NestedCli(data, 'Select Experiment', False)
    pprint(expinfo.out)



