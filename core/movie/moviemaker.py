#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Florian Perdreau (f.perdreau@donders.ru.nl)


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