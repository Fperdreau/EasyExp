# Optotrack Wrapper
## Author:
Florian Perdreau - [www.florianperdreau.fr](http://www.florianperdreau.fr)

## Description:
This is a wrapper class handling routines of the SR-Research(R) EyeLink series.

## License:
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

### Dependencies
* Qeyelink: Copyright &copy; 2012-2015 Wilbert van Ham, licenced under the [GNU GPL 3.0 ](http://www.gnu.org/licenses/).

# Issues:
- the method draw_image_line() (in display_psychopy.py) used to display of eye image sometimes (not always) throws the following error:
>
`
File "display\display_psychopy.py", line 366, in draw_image_line
    self.imagebuffer.tostring(), self.size, 'RGBX')
ValueError: String length does not equal format and resolution size
`

# To do
- Write commands on the Calibration startup screen

