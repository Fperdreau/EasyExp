# EasyExp - Changelog

## Version 1.0.3 - Beta
- Fixed issues related to state transition (e.g. pauses). self.move_on() must now be used instead of self.change_state(force_move_on=True) in order to force transition 
to next state.
- Method instance and its attributes/methods can now be accessed from RunTrial by calling self.trial.method.get('instance_id'). 

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
