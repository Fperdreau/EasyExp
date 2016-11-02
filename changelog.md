# EasyExp - Changelog

## Version 1.0.4
- Corrected updating of settings dictionary with values specified in settings.json
- BaseTrial: only call MethodContainer.update() if a staircaseID is specified in the design file. This prevent calling the Methods/Constant.update()
- Added a specific version number to every EasyExp modules (apart from Core modules) to facilitate the tracking of changes.

### Devices
- Sled: Added Sled.validate() method to validate state of sled (position and null velocity) over a given period of time. 
- Sled: Added Sled.at_position() method to test whether the sled is not moving and at a specified position.
- Sled: Improved estimation of velocity by measuring actual time interval between two stored samples.

## Version 1.0.3 - Betas
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
