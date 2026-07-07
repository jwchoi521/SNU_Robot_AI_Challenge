// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from snu_robot_interfaces:msg/GripperCommand.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_COMMAND__STRUCT_H_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_COMMAND__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Constant 'OPEN'.
enum
{
  snu_robot_interfaces__msg__GripperCommand__OPEN = 1
};

/// Constant 'CLOSE'.
enum
{
  snu_robot_interfaces__msg__GripperCommand__CLOSE = 2
};

/// Constant 'STOP'.
enum
{
  snu_robot_interfaces__msg__GripperCommand__STOP = 3
};

/// Constant 'SET_OPENING'.
enum
{
  snu_robot_interfaces__msg__GripperCommand__SET_OPENING = 4
};

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in msg/GripperCommand in the package snu_robot_interfaces.
/**
  * Command for the front basket/gripper mechanism.
 */
typedef struct snu_robot_interfaces__msg__GripperCommand
{
  std_msgs__msg__Header header;
  uint8_t command;
  /// Used by SET_OPENING. Ignored by simple OPEN/CLOSE grippers.
  float opening_m;
  /// Optional normalized effort or motor power, 0..1.
  float effort;
} snu_robot_interfaces__msg__GripperCommand;

// Struct for a sequence of snu_robot_interfaces__msg__GripperCommand.
typedef struct snu_robot_interfaces__msg__GripperCommand__Sequence
{
  snu_robot_interfaces__msg__GripperCommand * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} snu_robot_interfaces__msg__GripperCommand__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_COMMAND__STRUCT_H_
