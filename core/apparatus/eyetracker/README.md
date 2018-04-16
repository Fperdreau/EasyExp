# Eyelink wrapper class

## Author

Florian Perdreau - [www.florianperdreau.fr](http://www.florianperdreau.fr)

## Description

This is a wrapper class handling routines of the SR-Research(R) EyeLink series.

## License

Copyright (C) 2015 Florian Perdreau, Radboud University Nijmegen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

## Dependencies

* PyLink (for SR Research Eyelink eye-tracking system)

* Qeyelink: Copyright &copy; 2012-2015 Wilbert van Ham, licenced under the [GNU GPL 3.0](http://www.gnu.org/licenses/).

## How to use

See example in example_pygame.py

## Issues

* There is some latency when listening to key presses, and sometimes pressing the key multiple times in a row to trigger to wanted action (e.g. start calibration by pressing C)

## To do

* Complete implementation for pyQt.