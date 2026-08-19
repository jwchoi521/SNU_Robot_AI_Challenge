# Command for the front basket/gripper mechanism.

uint8 OPEN=1
uint8 CLOSE=2
uint8 STOP=3
uint8 SET_OPENING=4
uint8 UNLOAD=5

std_msgs/Header header
uint8 command

# Used by SET_OPENING. Ignored by simple OPEN/CLOSE grippers.
float32 opening_m

# Optional normalized effort or motor power, 0..1.
float32 effort
