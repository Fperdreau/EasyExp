# EasyExp - A Simple way of coding behavioral experiments in Python
Version: 0.9.0
Status: Development

## Author:
Florian Perdreau - [www.florianperdreau.fr](http://www.florianperdreau.fr)

## Description:
EasyExp is a framework designed to ease the programming of experiments using Python. It provides several wrapper
classes that handles routines to use equipments present in the sled lab (Sled, Eyetracker, Optotrak, Shutter glasses or LEDs)

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
* FPclient: Copyright &copy; 2012-2015 Wilbert van Ham, licensed under the [GNU GPL 3.0 ](http://www.gnu.org/licenses/).
* Qeyelink: Copyright &copy; 2012-2015 Wilbert van Ham, licensed under the [GNU GPL 3.0 ](http://www.gnu.org/licenses/).
* SledClient: Copyright &copy; 2012-2015 Wilbert van Ham, licensed under the [GNU GPL 3.0 ](http://www.gnu.org/licenses/).
* SledClientSimulator: Copyright &copy; 2012-2015 Wilbert van Ham, licensed under the [GNU GPL 3.0 ](http://www.gnu.org/licenses/).
* rusocsci: Copyright &copy; 2013 Wilbert van Ham, licensed under the [GNU GPL 3.0 ](http://www.gnu.org/licenses/).
* PsiMarginal: Copyright &copy; 2016 Nynke Niehof, licensed under the [GNU GPL 3.0 ](http://www.gnu.org/licenses/).
* pyMouse: Copyright 2010 Pepijn de Vos [Apache License 2.0 ] (http://www.apache.org/licenses/LICENSE-2.0)

## To do
* Write documentation
* It would perhaps be better to move ExpCore and its associated dependencies out of this project and make a separated
one.

## Framework structure
```
../Name_of_project(ROOT)
    /analyses: this folder should contain your analysis scripts. Some examples about how to import data into MATLAB (R)
     are provided here.
    /core: Core classes and modules of EasyExp can be found here.
    /data: EasyExp will save participants data here, with one folder per participant.
    /experiments: This folder should contain one folder per experiment
        /experiment_name: This folder should contain the following files
            /conditions.json: condition file (see below for more details)
            /custom_design.py (optional): Custom design generator should be handled by this function.
            /parameters.json: experiment's parameters should be defined here (see below for more details)
            /runtrial.py: where your experiment is actually coded.
            /runtrial_threaded.py: threaded implementation of your experiment (if used, then this file should be renamed
             'runtrial.py' and replace the standard runtrial.py file.
            /settings.json: EasyExp settings
    /libs: this folder should contain librairies used by your experiments if they are not Python's built-in modules.
    /tests: this folder should contain your test scripts.
```

### Built-in libraries
#### Apparatus
This folder contains wrapper classes handling routines to use equipments.
- Eyetracker
- LEDS
- Optotrack
- Shutter glasses
- Sled

#### Buttons
- Buttons: Implementation of the response interface that can be used similarly whether it implements a mouse or a keyboard.

#### COM
This folders contains useful classes handling communication
- FPClient
- Rusocsci

#### Display
- QtWindow: Base class implementing QT-OpenGL application.
- Icon: folders including different icons for QT GUI

#### Events
This folder contains classes/modules implementing experiments' events.
- Pause: Implement breaks

#### GUI
This folder contains implementation of experiment's GUI
- DialogGUI: Dialog window

#### Methods
- Constant: implements constant stimuli design
- PsiMarginal: implements psi-method
- Random: implements random sampling method
- StaircaseASA: implements Accelerated Stochastic Approximation method

#### MISC
This folder contains miscellaneous classes/modules.
- Conversion: collection of conversion functions

#### Movie
- MovieMaker: handles the creation of movie demos

#### OpenGL
This folder contains classes handling the creation and use of OpenGL object.
- MyObject: wrapper class that creates OpenGL object callable by OpenGL operations
- Objects: collection of functions handling the creation of object's shapes.
- Shader: implements OpenGL shaders
- Transforms: handles object transformations.

#### Sound
This folder contains a collection of audio stimuli.

#### Stimuli
- Stimulus: handles stimulus-related routines.

#### System
This folder contains system-related classes.
- CustomLogger: wrapper class implementing Python's logger.

### Core Modules
Every classes/modules of EasyExp can be used separately, either within an object-oriented programming framework or simply in procedural scripts.

#### Core
#### Trial
#### User
#### Design
#### Trial
#### Config
#### ConfigFiles

## Setting up an experiment
### Settings file
#### conditions.json
Experiment design's parameters should be specified in this JSON file. This file is a JSON file and therefore it should respect the JSON format.
The general format is: "property_name": property_value. property_value can be any type of variables (scalar, string, array, nested arrays, ...)

```
{
  "timing": [
    0.150,
    0.400,
    0.650
  ],
  "first": [
    "bottom",
    "top"
  ],
  "repetition": 1,
  "side": [
    "left",
    "right"
  ],
  "mvt": [
      true
  ],
  "method": "StaircaseASA",
  "options": {
    "stimRange": [
      -2.8,
      2.8
    ],
    "maxInitialStepSize": 1.5,
    "stoppingStep": 0.1,
    "threshold": 0.50,
    "nTrials": 40,
    "limits": true,
    "nbStairs": 2,
    "warm_up": 2,
    "response_field": "correct",
    "intensity_field": "intensity"
  }

}

```


