# Command for four independently driven wheels.
#
# A low-level motor driver should convert this command to actual motor control.
# Use VELOCITY_RAD_S when the motor driver has velocity control.
# Use NORMALIZED_POWER when the motor driver accepts open-loop power/PWM.

uint8 VELOCITY_RAD_S=1
uint8 NORMALIZED_POWER=2

std_msgs/Header header
uint8 command_mode

float32 front_left
float32 front_right
float32 rear_left
float32 rear_right
