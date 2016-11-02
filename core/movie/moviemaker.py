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


class MovieMaker(object):
    """
    MovieMaker class
    Save frames into files in order to make of movie
    """

    allowed_type = {'tif', 'gif', 'png'}

    def __init__(self, ptw, name, movie_type):
        """
        Class constructorlandLineWidth
        :param ptw:
        :param name:
        :param movie_type:
        :return:
        """
        self.ptw = ptw
        self.name = name
        self.frame = 0
        if movie_type in self.allowed_type:
            self.type = movie_type
        else:
            raise "{} is not a supported type. You should use {} instead".format(type, self.allowed_type)
        self.prepare()

    def prepare(self):
        """
        Create destination folder
        :return:
        """
        import os
        if not os.path.isdir(self.name):
            os.mkdir(self.name)

    def run(self):
        """
        Captures a frame into a numbered file
        :return:
        """
        # Make Movie
        self.frame += 1
        filename = "{}/{}_{}.{}".format(self.name, self.name, self.frame, self.type)
        self.ptw.getMovieFrame()
        #self.ptw.saveMovieFrames(filename)

    def close(self):
        """
        Saves the captured frame into a file
        :return:
        """
        filename = "{}/{}_{}.{}".format(self.name, self.name, self.frame, self.type)
        self.ptw.saveMovieFrames(filename)