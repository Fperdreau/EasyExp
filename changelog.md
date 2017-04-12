# EasyExp - Changelog

## Version 1.2.0
- Add possibility to not load trial parameters from file
- Improved thread synchronization
- Improved memory usage and fixed issue with memory continuously
increasing with time.
- Added new stimuli container and removed RunTrial.stimuliTrigger container.
See RunTrial.init_stimuli() documentation for more information.
- Added default stimuli callable by RunTrial.default_stimuli[stimulus_name]

### Devices
- EyeTracker (v1.3.0):
    * Fixed display of eye image and handling of key inputs
    * EyeTracker.stop_trial() now complies with Devices interface.
    * Added position validator and velocity estimator for Eye class.
    * Added Eyetracker.calibrate() method
- Sled (v1.1.5): Added work-around to prevent error when accessing PositionTracker.position property.
- JoyStick (v1.1.0): Improved JoyStick device and added position validator.

## Version 1.1.0
- Corrected updating of settings dictionary with values specified in settings.json
- BaseTrial: Assume trial as valid by default. User can define validity of current trial by setting BaseTrial.validTrial
 to True or False before entering into the "end" state.
- BaseTrial: only call MethodContainer.update() if a staircaseID is specified in the design file. This prevent calling the Methods/Constant.update()
- Added a specific version number to every EasyExp modules (apart from Core modules) to facilitate the tracking of changes.

### Methods
- StaircaseASA (v1.1.0): corrected error due to wrong computations of completed trials.
- MethodeBase: added application logger

### Devices
- LinearGuide (v1.0.1): LinearGuide.valideposition() can take threshold_time as argument to set minimum duration for 
detecting slider movement. 
- OptoTrak (v1.1.0): Improved velocity computation
- Sled (v1.1.4): Added Sled.validate() method to validate state of sled (position and null velocity) over a given period of time. 
- Sled (v1.1.4): Added Sled.at_position(position, tolerance) method to test whether the sled is at a specified position.
- Sled (v1.1.4): Added Sled.wait_ready(position, duration) method. Test if sled is at expected position. If not, then move to this location.
- Sled (v1.1.4): Improved estimation of velocity by measuring actual time interval between stored samples.

## Version 1.0.3 - Beta
- Fixed issues related to state transition (e.g. pauses). self.move_on() must now be used instead of self.change_state(force_move_on=True) in order to force transition 
to next state.
- Method instance and its attributes/methods can now be accessed from RunTrial by calling self.trial.method.get('instance_id'). 
- Pause duration, mode and interval can now be specified in settings.json. Breaks are now triggered either after a specified delay is mode is set to "time", or after a specified number of completed trials if mode is set to "count".

## Version 1.0.2 - Beta
- Fixed bug preventing the continuous display of stimuli

## Version 1.0.1 - Beta
### Devices
- Improved handling of devices used in the experiment. Devices must now be defined in devices.json. They will be automatically loaded and initialized.
- Feature: Added possibility to continuously update stimuli without break or screen blank between trials. Continuous update can be enable by setting RunTrial.clearAll 
to False in RunTrial's constructor

## Version 1.0.0 - Beta
### Methods
- Improved handling of experiment methods (staircases).
- Fixed bug in StairCaseASA that was slowing down the convergence
- Added PsiMarginal method

### State machine (RunTrial and BaseTrial)
- Improved the state machine and multi-threading. Multiple singleshot events can now be triggered within a same state.
- Added default states to both fast and graphics state machines: only custom states defined by the user should be implemented
in RunTrial.fast_state_machine() and RunTrial.graphics_state_machine()
- Added a fancy loading screen during the experiment initialization.
- Fixed stimuli rendering order: stimuli are now rendered in the same order as their corresponding triggers defined in RunTrial.stimuliTrigger container.

### Apparatus
- SLED: added is_moving property. It allows checking if the sled is not moving before sending a new command.
- SLED: added get_velocity() method to retrieve sled's instantaneous velocity.
