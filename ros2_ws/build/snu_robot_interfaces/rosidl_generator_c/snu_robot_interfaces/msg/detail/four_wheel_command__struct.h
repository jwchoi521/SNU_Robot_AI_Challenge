// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from snu_robot_interfaces:msg/FourWheelCommand.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__FOUR_WHEEL_COMMAND__STRUCT_H_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__FOUR_WHEEL_COMMAND__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Constant 'VELOCITY_RAD_S'.
enum
{
  snu_robot_interfaces__msg__FourWheelCommand__VELOCITY_RAD_S = 1
};

/// Constant 'NORMALIZED_POWER'.
enum
{
  snu_robot_interfaces__msg__FourWheelCommand__NORMALIZED_POWER = 2
};

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in msg/FourWheelCommand in the package snu_robot_interfaces.
/**
  * Command for four independently driven wheels.
  *
  * A low-level motor driver should convert this command to actual motor control.
  * Use VELOCITY_RAD_S when the motor driver has velocity control.
  * Use NORMALIZED_POWER when the motor driver accepts open-loop power/PWM.
 */
typedef struct snu_robot_interfaces__msg__FourWheelCommand
{
  std_msgs__msg__Header header;
  uint8_t command_mode;
  float front_left;
  float front_right;
  float rear_left;
  float rear_right;
} snu_robot_interfaces__msg__FourWheelCommand;

// Struct for a sequence of snu_robot_interfaces__msg__FourWheelCommand.
typedef struct snu_robot_interfaces__msg__FourWheelCommand__Sequence
{
  snu_robot_interfaces__msg__FourWheelCommand * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} snu_robot_interfaces__msg__FourWheelCommand__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__FOUR_WHEEL_COMMAND__STRUCT_H_
