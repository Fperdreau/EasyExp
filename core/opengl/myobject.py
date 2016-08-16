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

# openGL
import OpenGL
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.arrays import vbo
from OpenGL.GL.shaders import *
import transforms, objects, shader
import numpy as np


class MyObject(object):
    """
    MyObject wrapper class creates OpenGL object callable by OpenGL operations

    Usage
    >>>stimuli = MyObject('sphere', 0.5)
    >>>stimuli.make()
    """

    def __init__(self, shape='sphere', size=None):
        """
        MyObject constructor
        :param shape: object shape
        :param size: object size
        :return:
        """
        self.shape = shape
        self.indices = None
        self.vertices = None
        self.color = None
        self.size = size

    def make(self):
        """
        This function creates vertices and indices
        :return:
        """
        if self.shape is "sphere":
            v, t, n, tex = objects.sphere(self.size)
            self.vertices = vbo.VBO(v, target=GL_ARRAY_BUFFER, usage=GL_STATIC_DRAW)
            self.indices = vbo.VBO(t, target=GL_ELEMENT_ARRAY_BUFFER)
        elif self.shape is "parallelepiped":
            v, t, = objects.parallelepiped(self.size)
            self.vertices = vbo.VBO(v, target=GL_ARRAY_BUFFER, usage=GL_STATIC_DRAW)
            self.indices = vbo.VBO(t, target=GL_ELEMENT_ARRAY_BUFFER)
        elif self.shape is "cross":
            # Fixation cross
            v, t = objects.cross()
            self.vertices = vbo.VBO(v, target=GL_ARRAY_BUFFER, usage=GL_STATIC_DRAW)
            self.indices = vbo.VBO(t, target=GL_ELEMENT_ARRAY_BUFFER)
        elif self.shape is 'line':
            v = np.array([
                    [-1.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0]
                ], dtype='float32')
            t = np.array([0, 1], np.int32)
            self.vertices = vbo.VBO(v*self.size, target=GL_ARRAY_BUFFER, usage=GL_STATIC_DRAW)
            self.indices = vbo.VBO(t, target=GL_ELEMENT_ARRAY_BUFFER)
        else:
            raise Exception('{} is not a valid object shape'.format(self.shape))
