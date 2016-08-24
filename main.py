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

# Import libraries
from os.path import dirname, abspath
import sys

# EasyExp Core
from core.Core import Core

# Import libraries used by this experiment
root_folder = dirname(abspath('__file__'))
sys.path.append("{}/libs".format(root_folder))


def main():
    """
    Main function: call experiment's routines
    """

    # Get CLI arguments
    cli = True if len(sys.argv) > 1 and sys.argv[1] == 'cli' else False

    # Create new experiment
    experiment = Core()

    # Initialize experiment
    experiment.init(root_folder, custom=True, cli=cli)

    # Open main window and run the experiment
    experiment.run()


if __name__ == '__main__':
    main()
