// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from snu_robot_interfaces:msg/GripperState.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_STATE__STRUCT_H_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_STATE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in msg/GripperState in the package snu_robot_interfaces.
/**
  * State reported by the front basket/gripper mechanism.
 */
typedef struct snu_robot_interfaces__msg__GripperState
{
  std_msgs__msg__Header header;
  bool is_open;
  bool is_closed;
  bool has_object;
  float opening_m;
  float effort;
} snu_robot_interfaces__msg__GripperState;

// Struct for a sequence of snu_robot_interfaces__msg__GripperState.
typedef struct snu_robot_interfaces__msg__GripperState__Sequence
{
  snu_robot_interfaces__msg__GripperState * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} snu_robot_interfaces__msg__GripperState__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_STATE__STRUCT_H_
