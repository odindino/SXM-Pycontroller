# Development note for SXM-Pycontroller

## This file is used to make a user-friendly module for SXM controlling

### Scenarios

#### 1. Conduct a spectroscopy measurement(point, line or array) at a given position with varying Vds or Vg bias

>1-1. After moving the tip to the position, turn off the feedback loop
1-2. Conduct the command for SMU, set the Vds or Vg bias, and turn on the SMU
1-3. Conduct the spectroscopy measurement
1-4. Turn off the SMU
1-5. Turn on the feedback loop
1-6. Repeat the above steps for different Vds or Vg bias, if any.
1-7. Move the tip to the next position and repeat the above steps.

To archieve this, we need:

1. Ability to move the tip to certain place, like point, line, or array.
2. Do the STS with turn on and off feedback and controlling the SMU
3. The STM scanning process should be available after any STS measurement.
