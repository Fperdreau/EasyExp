#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Florian Perdreau
# Date: 21/01/2015

from Tkinter import *


class DialogGUI(object):
    """
    Display a dialog GUI
    """

    def __init__(self, defaultfields, title="DialogUI"):
        self.root = Tk()
        self.entries = []
        self.out = {}
        self.types = []
        self.title = title
        self.fields = defaultfields
        self.makeform()
        self.displayform()

    def makeform(self):
        self.root.title(self.title)

        for field, value in self.fields.iteritems():
            row = Frame(self.root)
            lab = Label(row, width=15, text=field, anchor='w')
            row.pack(side=TOP, fill=X, padx=5, pady=5)
            lab.pack(side=LEFT)

            #  Guess the entry type
            if type(value) is not str and isinstance(value, set):
                # If array, then create a selection list
                self.types.append('set')
                ent = StringVar(self.root)
                ent.set(list(value)[0])  # default value
                w = apply(OptionMenu, (self.root, ent) + tuple(value))
                w.pack()
            elif type(value) is not str and isinstance(value, bool):
                # if boolean, then create radio buttons
                self.types.append('bool')
                ent = BooleanVar(self.root)
                ent.set(value)
                Radiobutton(self.root, text="Yes", padx=20, variable=ent, value=True).pack(anchor='w')
                Radiobutton(self.root, text="No", padx=20, variable=ent, value=False).pack(anchor='w')
            else:
                if isinstance(value, int):
                    self.types.append('int')
                    t = IntVar(self.root)
                elif isinstance(value, float):
                    self.types.append('float')
                    t = DoubleVar(self.root)
                elif isinstance(value, list):
                    self.types.append('list')
                    value = ','.join(str(e) for e in value)
                    t = StringVar(self.root)
                else:
                    self.types.append('str')
                    t = StringVar(self.root)
                ent = Entry(row, textvariable=t)
                t.set(value)
                ent.pack(side=RIGHT, expand=YES, fill=X)
            self.entries.append((field, ent))

    def displayform(self):
        self.root.bind('<Return>', (lambda event,
                                           e=self.entries: self.fetch()))
        b1 = Button(self.root, text='Ok',
                    command=(lambda e=self.entries: self.fetch()))
        b1.pack(side=LEFT, padx=5, pady=5)
        b2 = Button(self.root, text='Quit', command=self.root.destroy)
        b2.pack(side=LEFT, padx=5, pady=5)
        self.root.mainloop()

    def fetch(self):
        i = 0
        for entry in self.entries:
            field = entry[0]
            out = entry[1].get()
            if self.types[i] == 'bool':
                out = bool(out)
            elif self.types[i] == 'int':
                out = int(out)
            elif self.types[i] == 'float':
                out = float(out)
            elif self.types[i] == 'list':
                out = [float(e) for e in out.split(',')]
            else:
                out = str(out)
            self.out[field] = out
            i += 1
        self.root.destroy()
