#!/usr/bin/python
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

from Config import ConfigFiles


class Parameters(object):
    """
    Parameters class
    
    Requires: parameters.json file stored in experiment folder
    """

    def __init__(self, path):
        """
        Class constructor
        :param path: full path to parameters.json file
        """
        self.__parameters = self.__load(path)

    @staticmethod
    def __load(paramsfile):
        """
        Get experiment's parameters
        :param string paramsfile: full path to parameters.json file
        :return:
        """
        if paramsfile is not None:
            paramsfile = ConfigFiles(paramsfile)
            parameters = paramsfile.load()
        else:
            parameters = None
        return parameters

    def __getitem__(self, item):
        """
        Parameters getter
        :param item: 
        :return: 
        """
        if self.__parameters is not None and item in self.__parameters:
            return self.__parameters[item]
        else:
            return None

    def __iter__(self):
        """
        Iteration method: returns triggers value in order
        :return:
        """
        for item_id, item in self.__parameters.iteritems():
            yield item

    def iteritems(self):
        """
        Iteration method: returns triggers name and value in order
        :return:
        """
        for item_id, item in self.__parameters.iteritems():
            yield item_id, item

    def __str__(self):
        out = []
        for key, value in self.iteritems():
            out.append('{}: {}'.format(key, value))
        return ' '.join(str(n) for n in out)


if __name__ == '__main__':
    file_name = '../experiments/demo/parameters.json'
    parameters = Parameters(file_name)
    print(parameters)
    print(parameters['mvtBackDuration'])
