import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/cho/SNU_Robot_AI_Challenge/ros2_ws/install/snu_target_navigation'
