# EasyExp - Changelog

## Version 1.0.1 - Beta
### Devices
- Improved handling of devices used in the experiment. Devices must now be defined in devices.json. They will be automatically loaded and initialized.

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
