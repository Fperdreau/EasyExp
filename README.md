# EasyExp - A Simple way of coding behavioral experiments in Python
**Version**: 1.2.0

**Status**: Production

## Author:
Florian Perdreau - [www.florianperdreau.fr](http://www.florianperdreau.fr)

## Description:
_EasyExp_ is a Python framework for coding **multi-threaded** experiments with [PsychoPy](http://www.psychopy.org/) or [PyQt](https://riverbankcomputing.com/software/pyqt/intro). 

Experiments do not always only consist in presenting visual or audio stimuli but may also call external devices (eye-tracker, 
body-tracker, etc...) that need to run at close to real-time speed. In conventional programming of visual experiments, this is not possible 
because the main thread's running speed is limited by the screen's refresh rate. EasyExp overcomes this issue by relying on a multi-threaded state machine. 
Sounds complicated? Not at all! **EasyExp provides a simple, but complete framework making coding experiments easy!**

_EasyExp_ implements and handles experiment's routine (creation of participant, generation of experimental design, resume function, breaks) that are fully 
customizable without necessarily changing the code of your experiment. EasyExp also comes with a collection of modules handling interfaces,
experimental methods or devices that could be used in an experiment. All of this modules are designed to be autonomous and
independent from _EasyExp_. This means that everyone is free to use these modules in their experiment without using the 
whole framework.

## License:
Copyright (C) 2016 Florian Perdreau, Radboud University Nijmegen

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

## Requirements
### General
* Python 2.7 32 bits
* Numpy
* Scipy

### Apparatus
* PyLink (EyeLink, SR-Research)
* PyMouse - cross-platform solution for controlling mouse
* PyHook (required by PyMouse)
* PySerial

### Display
* PsychoPy 1.17+
* Pygame 1.8+
* PyOpenGl
* PyQt

## Dependencies
* FPclient: Copyright &copy; 2012-2015 Wilbert van Ham, licensed under the [GNU GPL 3.0 ](http://www.gnu.org/licenses/).
* Qeyelink: Copyright &copy; 2012-2015 Wilbert van Ham, licensed under the [GNU GPL 3.0 ](http://www.gnu.org/licenses/).
* SledClient: Copyright &copy; 2012-2015 Wilbert van Ham, licensed under the [GNU GPL 3.0 ](http://www.gnu.org/licenses/).
* SledClientSimulator: Copyright &copy; 2012-2015 Wilbert van Ham, licensed under the [GNU GPL 3.0 ](http://www.gnu.org/licenses/).
* rusocsci: Copyright &copy; 2013 Wilbert van Ham, licensed under the [GNU GPL 3.0 ](http://www.gnu.org/licenses/).
* PsiMarginal: Copyright &copy; 2016 Nynke Niehof, licensed under the [GNU GPL 3.0 ](http://www.gnu.org/licenses/).
* pyMouse: Copyright 2010 Pepijn de Vos [Apache License 2.0 ] (http://www.apache.org/licenses/LICENSE-2.0)

## Framework structure
EasyExp works as a standalone application: it means that you will have one copy of EasyExp per project. A project is structured as follows:

```
../Name_of_project(ROOT)
    /analyses: this folder should contain your analysis scripts. Some examples about how to import data into MATLAB (R)
     are provided here.
    /core: Core classes and modules of EasyExp can be found here.
    /data: EasyExp will save participants data here, with one folder per participant.
    /experiments: This folder should contain one folder per experiment
        /experiment_name: This folder should contain the following files
            conditions.json: condition file (see below for more details)
            custom_design.py (optional): Custom design generator should be handled by this function.
            parameters.json: experiment's parameters should be defined here (see below for more details)
            runtrial.py: where your experiment is actually coded.
            devices.json: list of devices used in this experiment and their settigns.
            settings.json: your experiment settings
    /libs: this folder should contain librairies used by your experiments if they are not Python's built-in modules.
    /logs: Experiment's logs will be stored here.
        __experiment_name__data__time.log: all events and errors occuring during your experiment will be recorded in this file.
    /tests: this folder should include unit test scripts.
```

## Setting up an experiment
### Step 1: install EasyExp Framework
#### Get EasyExp
##### Using git:

Open a terminal (Linux) or your command line interface (Windows) and type:

```
cd path/to/my/project/folder

git clone https://gitlab.socsci.ru.nl/fperdreau/EasyExp.git
```

##### or download from GitLab:

1. Go to: https://gitlab.socsci.ru.nl/fperdreau/EasyExp/repository/archive.zip?ref=master
2. Unzip the archive into your project folder

### Step 2: Create your first experiment
#### Preparation of project
1. Go to your project folder
2. Rename the EasyExp folder to match your project name

#### Create a new experiment
One study often involves several experiments involving the same participants. Experiments are stored in /your_project(ROOT)/experiments/ folder.
You can find a experiment template in /your_project(ROOT)/experiments/experiment_name.
To create a new experiment, you can copy/paste this template folder in the experiments folder and rename it by giving the name you want (e.g. "experiment_1", or "condition_1")

An experiment folder contains all the files you need to implement your experiment:
- runtrial_template_psychopy.py: Template for experiment using *PsychoPy*. If you use this one, then it must be renamed "runtrial.py"
- runtrial_template_qt.py: Template for experiment using *PyQt*. If you use this one, then it must be renamed "runtrial.py"
- conditions.json: experiment conditions and method
- devices.json: list of devices used in this experiment as well as their settings
- parameters.json: parameters used in runtrial.py
- settings.json: experiment's settings (session number, demo mode, etc..)

### Step 3: Settings files
EasyExp is based on the idea of separating code from data and parameters as much as possible. 
This will give much more flexibility to your experiments (changing parameters without changing the code),
and it will allow you focusing more on the content rather than on the logic. 
For this reason, only few files need to be edited in order to start a new experiment.

#### settings.json
Every time you run an experiment, you will be prompted with a dialog window allowing you to confirm or modify the experiment's settings. 
Experiment's settings are stored in "settings.json", which is a JSON file structured in 3 different section:
- Setup: contains experiment-related settings (demo mode, session id, etc.)
- Display: contains display-related settings (screen resolution and size, refresh rate, windows type, etc)

Every settings stored in these sections is structured as follows:

```
"setting_name": {
    "type": field_type,
    "value": current_value,
    "label": "input_label",
    "options": ["option 1", 2, true]
}
```

* type: defines how this input field should be rendered ("text": a simple text input, "select": a selection menu 
displaying the possible options specified by the "options" field, "checkbox": display one checkbox per options)

* value: default or previously selected value

* label: Label (string) that will be displayed next to the input field.

* options (optional): list of possible options. Options can be of any type (string, boolean, int, float)

See settings.json file in the template ('experiment_name') folder for the full list of possible settings:

#### conditions.json

Experiment design's parameters should be specified in this JSON file. This file is a JSON file and therefore it should respect the JSON format.
The general format is: "property_name": property_value. property_value can be any type of variables (scalar, string, array, nested arrays, ...)

```
{
  "factor_name_with_multiple_level": [
    "left",
    "right"
  ],
  "factor_name_with_single_level": [true],
  "method": "method_name",
  "options": {
    "nTrials": 40,
    "response_field": "correct",
    "intensity_field": "intensity"
  }

}
```

__List of fields:__
* method (required): specify the experimental method used to generate your design and trials list. Options are 'Constant'
 (Constant stimuli), 'PsiMarginal' (psi-method), 'StaircaseASA' (accelerated stochastic approximation), or 'Random' (random sampling)
* options (optional): method's options. If not specified, then method's default settings will be used. See methods 
documentation for more details about the possible options.

#### devices.json

Your experiment might use some external devices (eyetracker, vestibular chair, joystick, etc.) that you can control using a Python API. Some device APIs are already implemented in EasyExp.
You can find the list in core/apparatus/. See also [Device API for EasyExp]"Device API for EasyExp" section for more details about how to make your API compatible with EasyExp.

Every devices used in your experiment must be listed in devices.json as follows:

```
{
    "devices": {
        "class_name": {
            "options": {
                "argument1": value,
                "argument2": value
            }
        },
        "class_name": {
            "options": {
                "argument1": value,
                "argument2": value
            }
        }
    }
}
```

__List of fields:__
- "class_name": MUST match the actual class name of the device (case-sensitive)
- "options": Arguments defined in "options" are those passed to the device class constructor. See the documentation of each
device (in core/apparatus/device_name/device_name.py) to get the full list of arguments. Note that it is not
necessary to define all the arguments. Missing arguments will be automatically replaced by class's default values.

Example:
```
    "devices": {
        "OptoTrak":
            "options": {
                "freq": 60.0,
                "velocity_threshold": 0.01
            },
        "Sled": {
            "options": {
                "server": "sled"
            }
        }
    }
```

Devices are stored in the container RunTrial.devices, which acts like a dictionary. To access a device's method:
```
RunTrial.devices['device_name'].method_name(*args)
```

### Implementation of experiment procedure (runtrial.py)
#### Description
The RunTrial class handles experiment procedure. This is actually a multi-threaded state machine.

This class calls on two threads: one fast (close to real-time), one slow (limited by screen's refresh rate)
A same state can be present in both state machines, but it should only call rendering operation within the slow
state machine
For instance, if you want to record hand movement while displaying a stimulus on the screen, the rendering
operations should be implemented in RunTrial.graphics_state_machine(), whereas the recording of hand positions
should be coded in the fast_state_machine().

**IMPORTANT:**
The actual multi-threading implementation of this class is not perfectly thread-safe. For that reason, the two
state machines should be considered independent from each other and should not make operation on shared variables.
However, because the fast state machine runs much faster than the graphics state machine, then changes made within
the fast state machine will be accessible by the slowest state machine, BUT NOT NECESSARILY THE OTHER WAY AROUND!
Therefore, if objects have to be modified within a thread, this should be done in the fastest one.

#### RunTrial API
- RunTrial.__init__(): Class's constructor. Triggers and data field can be initialized here. In general,
any variables used by several class' methods should be initialized in the constructor as self._attribute_name
- RunTrial.init_devices(): devices used by the experiment should be instantiated here.
- RunTrial.init_stimuli(): Initialization/Preparation of stimuli. Creation of stimuli objects should be implemented
here.
- RunTrial.init_audio(): Initialization/Preparation of auditory stimuli and beeps. Creation of auditory objects
should be implemented here.
- RunTrial.get_response(): Participant's response should be handled here. This method is typically called during the
"response" state.
- RunTrial.fast_state_machine(): Real-time state machine.
- RunTrial.graphics_state_machine(): Slow state machine.

#### Constructor (RunTrial.__init__()):
Your customization starts here. Here, you can add your own attributes, triggers, buttons, etc. used in your experiment.

##### Display options
If set to False, then display will not be automatically cleared at the end of each trial. This allows
continuous rendering with no blank between trials.
```
self.clearAll = True
```

##### Experiment settings
Experiment's parameters can accessed by calling self.trial.parameters['parameter_name']
Because parameters are loaded from a JSON file, they are imported as string. Therefore, it might be necessary
to convert the parameter's type: e.g. as a float number.
Example:
```
self.my_parameter = float(self.trial.parameters['my_parameter']
```

##### Events triggers
Default triggers are moveOnRequested, pauseRequested, startTrigger and quitRequested (defined in BaseTrial class).
They should not be modified. However, you can add new triggers: 'trigger_name': False
```
self.triggers.update({
    'my_trigger_name': False
})
```

##### Stimulus triggers
Stimuli triggers can be added by calling:
```
self.stimuliTrigger.add('stimulus_name', 'value')
```
If value is not provided, then False will be set by default.
IMPORTANT: if 'stimulus_name' is added to self.stimuliTrigger, then it should also be added to self.stimuli
dictionary in RunTrial.init_stimuli() method

stimuliTrigger acts like a dictionary. item's value can be accessed by calling:
```
self.stimuliTrigger['stimulus_name']
```

and new trigger value can be set by calling:
```
self.stimuliTrigger['stimulus_name'] = True
```

if self.stimuliTrigger['stimulus_name'] is True, then self.stimuli['stimulus_name'].draw() will be called.

IMPORTANT: stimuli are rendered in the same order as the triggers defined in stimuliTrigger dictionary.
```
self.stimuliTrigger.add('my_circle')
```

#### Timers
RunTrial.timers is a dictionary handling of all the timers called during your experiment.

Add your timers to this dictionary.
Default timer is timers['runtime'] and it should not be removed
Example:
```
self.timers.update({
    'timer_name': Timer()
    }
)
```
Timer class works like a watch (see core/events/timer.py for more documentation):
```
# Then, to start the timer
timers['timer_name'].start()

# Stop the timer
timers['timer_name'].stop()

# Get elapsed time
print(timers['timer_name'].get_time('elapsed')

# Reset timer
timers['timer_name'].reset()
```

##### Data
Data field that will be output into the data file should be specified here.
```
self.data = {
    'field_name': None
}
```

##### Keyboard/Mouse Inputs
User inputs (button press or mouse click) are handled by RunTrial.buttons container.

Add a button to the watched list:
```
self.buttons.add_listener('device_type', 'key_label', key_code)  # arguments are: device_type, key label, key code (Pygame constant)
```

For example:
```
self.buttons.add_listener('keyboard', 'a', pygame.K_a)  # arguments are: device_type, key label, key code (Pygame constant)
self.buttons.add_listener('mouse', 'left', 0)  # Left mouse click
self.buttons.add_listener('mouse', 'right', 2)  # Right mouse click
```

Access watched inputs' status
```
# self.buttons.get_status('key_label')  # returns True or False
```

#### Fast state machine
Real-time state machine: state changes are triggered by keys or timers. States always have the same order.
This state machine runs at close to real-time speed. Event handlers (key press, etc.) and position trackers
(optotrak, eye-tracker or sled) should be called within this state machine.
Rendering of stimuli should be implemented in the graphics_state_machine()
Default state order is:
*1.* loading: preparing experiment (loading devices, ...)
*2.* idle: display welcome message and wait for user input
*3.* iti: inter-trial interval
*4.* init: load trial parameters
*5.* start: from here start the custom part. This state must be implemented in RunTrial.fast_state_machine()

...

*last.* end: end trial and save data

'loading', 'idle', 'init' and 'end' states are already implemented in BaseTrial.__default_fast_states() method,
but these implementations can be overwritten in RunTrial.fast_state_machines(). To do so, simply define these
states as usual. 

States are implemented as follows
```
if self.state == "state_name":
    self.next_state = 'next_state_name'
    
    if self.singleshot('singleshot_label'):
        # Instructions present in this block will be executed only once.
        
    # do something
    # Code here will be executed on every loop
```

#### Graphics state machine

The graphics state machine works similarly to the fast state machine except that its running speed is limited by the screen refresh rate. For
instance, this state machine will be updated every 17 ms with a 60Hz screen. For this reason, only slow events (display of stimuli) should be 
described here. Everything that requires faster (close to real-time) processing should be specified in the RunTrial::fast_state_machine() method.
Default state order is:
1. loading: preparing experiment (loading devices, ...)
2. idle: display welcome message and wait for user input
3. iti: inter-trial interval
4. init: load trial parameters
5. start: from here start the custom part. This state must be implemented in RunTrial.fast_state_machine()
...
last. end: end trial and save data

'loading', 'idle', and 'pause' states are already implemented in BaseTrial.__default_fast_states() method, but
these implementations can be overwritten in RunTrial.fast_state_machines().

#### BaseTrial API
RunTrial inherits most of its methods and attribute from BaseTrial abstract class. BaseTrial handles the logic of the state machine (state transitions)
 and of the multi-threading. Here is the list of its methods. See core/BaseTrial.py for more documentation.

- BaseTrial.__init__(): Class's constructor. Initialize triggers, inputs, devices, etc.
- BaseTrial.init_devices(): devices used in the experiment and defined in devices.json are initialized here.
- BaseTrial.init_trial(): Initialization of trial (get trial's information, reset triggers and data). This method
should not be modified
- BaseTrial.init_stimuli(): Must be implemented by RunTrial.
- BaseTrial.init_audio(): Must be implemented by RunTrial.
- BaseTrial.quit(): Quit experiment. This method is called when the experiment is over (no more trials to be played)
or when the user press the "quit" key.
- BaseTrial.go_next(): Check if transition to next state is requested (by key press or timer)
- BaseTrial.get_response(): Must be implemented by RunTrial.
- BaseTrial.end_trial(): End trial routine. Write data into file and check if the trial is valid or invalid.
- BaseTrial.run(): Application's main loop.
- BaseTrial.change_state(): handles transition between states.
- BaseTrial.fast_state_machine(): Real-time state machine.
- BaseTrial.graphics_state_machine(): Slow state machine.
- BaseTrial.__default_fast_states(): Definition of default state for fast_state_machine
- BaseTrial.__default_graphic_states(): Definition of default state for graphics_state_machine
- BaseTrial.update_graphics(): Render stimuli. More specifically, it check status of stimuli triggers and it a trigger is True, then it renders the corresponding 
stimulus stored in self.stimuli dictionary.

### Demo

A demo is provided along with the EasyExp. The demo experiments uses the SR-Research Eyelink 100 to control fixation, 
and the Sled to move the participant. However, you can run this demo on your office computer if you do not have access to the lab.
 To do so, when the settings dialog window is displayed (step 5), set "Sled" and "Eyetracker" settings to "Off", 
then the Sled will run in dummy mode (will simulate the observer's displacement and update the fixation point accordingly),
whereas the eye-tracker will not be used at all.

To run it:
1. Start your console
2. Go to your project folder
3. Type
    ```
    python main.py
    ```
    or
    ```
    python main.py cli
    ```
    to start the command-line interface
4. You will be prompted with an experiment selection dialog window: choose demo and click "Ok"
5. Then, you will be prompted with the settings dialog window. If you 
are not running this demo in the lab but on your desk computer, make sure
 that the equipments (sled, eyetracker, optotrak) are set to off.
6. At the beginning of the experiment, the message "Welcome" will be displayed. Simply click on the left button of the mouse to start
7. So trigger a break, simply press the space bar. If you want to quit the experiment, press Q ("A" on azerty keyboards)
 
### API
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
#### Screen
#### Devices
#### BaseTrial
#### Config
#### ConfigFiles
#### StateMachine

### Device API for EasyExp
#### Expected methods:
- Device.close(): this method should implement the closing method of the device. If does not take arguments.
- Device.start_trial(trial_id, trial_parameters): routine called at the beginning of a trial. Parameters are:
    int trial_id: trial number (or unique id)
    dict trial_parameters: Trial.params
- Device.stop_trial(trial_id, valid_trial): routine called at the end of a trial. Parameters should be:
    int trial_id: trial number (or unique id)
    bool valid_trial: is it a valid trial or not (e.g.: should it be excluded from analysis).

#### Expected class attributes:
- Devices.user_file (string): full name of file in which device data will be recorded (including absolute path: /path/to/file/file_name). If Device class has such attribute,
then core.Devices container will automatically generate a file name and pass it to Device.__init__(). The format of the generated file name is: 
```
(participant_name)_(experiment_name)_(session_id)_(device)_(date).ext
```
- Devices.dummy_mode (bool): If there is an implementation of a Dummy mode for your device, then you can add this class attribute.