// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from snu_robot_interfaces:msg/DetectedTargetArray.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET_ARRAY__STRUCT_H_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET_ARRAY__STRUCT_H_

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
// Member 'targets'
#include "snu_robot_interfaces/msg/detail/detected_target__struct.h"

/// Struct defined in msg/DetectedTargetArray in the package snu_robot_interfaces.
typedef struct snu_robot_interfaces__msg__DetectedTargetArray
{
  std_msgs__msg__Header header;
  snu_robot_interfaces__msg__DetectedTarget__Sequence targets;
} snu_robot_interfaces__msg__DetectedTargetArray;

// Struct for a sequence of snu_robot_interfaces__msg__DetectedTargetArray.
typedef struct snu_robot_interfaces__msg__DetectedTargetArray__Sequence
{
  snu_robot_interfaces__msg__DetectedTargetArray * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} snu_robot_interfaces__msg__DetectedTargetArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET_ARRAY__STRUCT_H_
