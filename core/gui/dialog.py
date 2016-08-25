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

from Tkinter import *
from ttk import Frame, Style

__author__ = "Florian Perdreau"
__copyright__ = "Copyright 2015, Florian Perdreau"
__license__ = "GPL"
__version__ = '1.1'
__maintainer__ = "Florian Perdreau"
__email__ = "f.perdreau@donders.ru.nl"


class BaseGui(object):
    """
    Base class for GUI handling user inputs
    """

    def __init__(self):
        """
        BaseGui constructor
        """
        self.root = Tk()
        self.entries = dict()
        self.out = dict()
        self.types = []

        self.title = None
        self.footer = None
        self.canvas = None
        self.mainFrame = None
        self.scrollbar = None
        self.scrolledFrame = None

    def initUI(self, size):
        """
        Init application GUI
        :return void
        """
        self.root.title(self.title)

        self.root.minsize(400, 210)

        self.set_geometry(size)

        style = Style()
        style.configure("TFrame", background="#FFF")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.title(self.title)
        self.root.configure(background='#FFF')

        # Footer (with ok and quit buttons)
        self.footer = Frame(self.root)
        self.footer.pack(side=BOTTOM, expand=YES)

        self.mainFrame = Frame(self.root)
        self.mainFrame.pack(side=TOP, fill=BOTH)

        # Main canvas
        self.canvas = Canvas(self.mainFrame, bd=1, scrollregion=(0, 0, 1000, 1000), height=600)
        self.canvas.pack(side=TOP, fill=BOTH)

        # creates canvas so that screen can be scrollable
        self.scrollbar = Scrollbar(self.mainFrame, command=self.canvas.yview)
        self.canvas.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.canvas.pack(expand=YES, fill=BOTH)

        # Settings frame
        self.scrolledFrame = Frame(self.canvas, width=100, height=100)
        self.scrolledFrame.pack(expand=1, fill=BOTH)

        self.canvas.create_window(0, 0, anchor=NW, window=self.scrolledFrame)

        self.populate()

    def set_geometry(self, size):
        """
        Set GUI geometry
        """

        # get screen width and height
        ws = self.root.winfo_screenwidth()  # width of the screen
        hs = self.root.winfo_screenheight()  # height of the screen

        self.root.maxsize(int(0.80 * ws), int(0.80 * hs))
        w = size[0]
        h = size[1]

        # calculate x and y coordinates for the Tk root window
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)

        # set the dimensions of the screen
        # and where it is placed
        self.root.geometry('%dx%d+%d+%d' % (w, h, x, y))

        self.root.update()

    def populate(self):
        """
        Populates form
        :return:
        """
        raise NotImplementedError("Should have implemented this")

    def onFrameConfigure(self, event):
        '''
        Reset the scroll region to encompass the inner frame
        '''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def displayform(self):
        self.root.bind('<Return>', (lambda event, e=self.entries: self.fetch()))
        b1 = Button(self.footer, text='Ok', command=(lambda e=self.entries: self.fetch()))
        b1.pack(side=LEFT, padx=5, pady=5)
        b2 = Button(self.footer, text='Quit', command=self.root.destroy)
        b2.pack(side=LEFT, padx=5, pady=5)
        self.root.mainloop()

    def input(self, entry, group, value=''):
        """
        Renders text input
        :param entry:
        :param group:
        :param value:
        :return:
        """
        entry.set(value)  # default value
        ent = Entry(group, textvariable=entry)
        ent.pack(side=RIGHT, expand=YES, fill=X)

    def select(self, entry, value, options, group=None):
        """
        Renders a dropdown menu
        :param entry:
        :param value:
        :param options:
        :param group:
        :return:
        """
        if group is None:
            group = self.root
        entry.set(value)  # default value
        ent = apply(OptionMenu, (group, entry) + tuple(options))
        ent.pack(side=RIGHT, expand=YES, fill=X)

    def checkbox(self, entry, value, options, group=None):
        """
        Renders a checkbox input
        :param value:
        :param entry:
        :param options:
        :param group:
        :return:
        """
        if group is None:
            group = self.root

        Btnframe = Frame(group)
        Btnframe.pack(side=LEFT)


        col = 0
        for option in options:
            if isinstance(option, bool):
                option_text = 'No' if not option else 'Yes'
            else:
                option_text = option
            button = Radiobutton(Btnframe, text=option_text, padx=20, variable=entry, value=option)
            button.grid(row=0, column=col)
            if option == value:
                button.select()
            col += 1

    def fetch(self):
        """
        Fetch user inputs
        :return:
        """
        raise NotImplementedError("Should have implemented this")

    def get_type(self, value):
        """
        Get value type
        :param value:
        :return:
        """
        #  Guess the entry type
        if type(value) is not str and isinstance(value, set):
            # If array, then create a selection list
            self.types.append('set')
            return StringVar(self.root), 'set'
        elif type(value) is not str and isinstance(value, bool):
            # if boolean, then create radio buttons
            self.types.append('bool')
            return BooleanVar(self.root), 'bool'
        elif isinstance(value, int):
            self.types.append('int')
            return IntVar(self.root), 'int'
        elif isinstance(value, float):
            self.types.append('float')
            return DoubleVar(self.root), 'float'
        elif isinstance(value, list):
            self.types.append('list')
            return StringVar(self.root), 'list'
        else:
            self.types.append('str')
            return StringVar(self.root), 'str'

    def parse_field(self, entry):
        """
        Parse field and convert input type
        :param entry:
        :return:
        """
        var_type = entry[2]  # input type
        out = entry[1].get()  # input value
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
            items = out.split(',')
            out = []
            for item in items:
                try:
                    value = float(item)
                except:
                    value = str(item)
                out.append(value)
        else:
            out = str(out)
        return out


class SimpleGui(BaseGui):
    """
    This class renders a GUI form from data provided by a JSON settings file. It handles methods to read and parse the
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
        info = SimpleGui(data)

        # Update settings file with inputs provided by the user (inputs are stored in info.out)
        with open(path_to_settings_file, 'w', 0) as fid:
            json.dump(info.out, fid, indent=4)
    ```
    """

    def __init__(self, default_fields, title="DialogUI", size=(400, 700)):
        """
        :param default_fields:
        :type default_fields: dict
        :param title:
        :type title: str
        :param size: window size
        :type size: tuple
        """
        super(SimpleGui, self).__init__()

        self.title = title
        self.data = default_fields

        self.initUI(size)
        self.displayform()

    def populate(self):
        """
        Renders form
        :return:
        """
        row = 0
        group = LabelFrame(self.scrolledFrame, padx=5, pady=5)
        group.pack(fill=X, padx=10, pady=10)
        for field_name, value in self.data.iteritems():
            frame = Frame(group)
            frame.pack(anchor=N, fill=X)

            # Render label
            lab = Label(frame, width=15, text=field_name)
            lab.pack(anchor='w', side=LEFT, padx=2, pady=2)

            # Guess the entry type
            entry, var_type = self.get_type(value)
            # Convert list to comma separated string
            if var_type == 'list':
                value = ','.join(str(e) for e in value)

            # Build input
            if var_type == 'bool':
                self.checkbox(entry, value, options=[True, False], group=frame)
            else:
                self.input(entry, group=frame, value=value)

            if field_name in self.entries:
                self.entries[field_name] = (field_name, entry, var_type)
            else:
                self.entries.update({
                    field_name: (field_name, entry, var_type)
                })

            row += 1

    def fetch(self):
        """
        Fetch form
        :return:
        """
        for field_name, entry in self.entries.iteritems():
            self.out[field_name] = self.parse_field(entry)
        self.root.destroy()


class NestedGui(BaseGui):
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
                    "options": [list_of_possible_inputs]
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

    def __init__(self, input_data, title="DialogUI", size=(400, 700)):
        """
        DialogGUI constructor
        :param dict input_data:
        :param str title:
        :return:
        """
        super(NestedGui, self).__init__()

        self.data = input_data  # Input
        self.out = input_data  # Output
        self.title = title

        self.initUI(size)
        self.displayform()

    def populate(self):
        """
        Populate form
        :return:
        """
        for key, section in self.data.iteritems():
            group = LabelFrame(self.scrolledFrame, text=key, padx=5, pady=5)
            group.pack(fill=X, padx=10, pady=10)

            row = 0
            for field_name, info in section.iteritems():
                frame = Frame(group)
                frame.pack(anchor=N, fill=X)

                label = info['label']
                value = info['value']
                input_type = info['type']

                # Render label
                lab = Label(frame, width=15, text=label)
                lab.pack(anchor='w', side=LEFT, padx=2, pady=2)

                # Guess the entry type
                entry, var_type = self.get_type(value)

                # Convert list to comma separated string
                if var_type == 'list':
                    value = ','.join(str(e) for e in value)

                # Build input
                if input_type == 'text':
                    self.input(entry, group=frame, value=value)
                elif input_type == 'select':
                    self.select(entry, value, info['options'], group=frame)
                elif input_type == 'checkbox':
                    self.checkbox(entry, value, options=info['options'], group=frame)

                if key in self.entries:
                    self.entries[key][field_name] = (field_name, entry, var_type)
                else:
                    self.entries.update({
                        key: {field_name: (field_name, entry, var_type)}
                    })
                row += 1

    def fetch(self):
        """
        Parse inputs
        :return:
        """
        for section, entry in self.entries.iteritems():
            for input_name, ent in entry.iteritems():
                self.out[section][input_name]['value'] = self.parse_field(ent)
        self.root.destroy()

if __name__ == '__main__':
    import json
    from pprint import pprint

    # Simple Gui
    pathtofile = "simple_settings.json"
    with open(pathtofile) as data_file:
        data = json.load(data_file)

    expinfo = SimpleGui(data)
    pprint(expinfo.out)

    # Nested Gui
    pathtofile = "nested_settings.json"
    with open(pathtofile) as data_file:
        data = json.load(data_file)
    expinfo = NestedGui(data)
    pprint(expinfo.out)

