// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from snu_robot_interfaces:msg/DetectedTarget.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET__STRUCT_H_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'object_kind'
// Member 'fruit_kind'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/DetectedTarget in the package snu_robot_interfaces.
/**
  * One target produced by the camera detector and distance provider.
  *
  * The current YOLO branch uses bearing_deg where positive means image-right.
  * Consumers can convert that convention with their own parameters.
 */
typedef struct snu_robot_interfaces__msg__DetectedTarget
{
  rosidl_runtime_c__String object_kind;
  rosidl_runtime_c__String fruit_kind;
  float confidence;
  float bbox_x1;
  float bbox_y1;
  float bbox_x2;
  float bbox_y2;
  float bearing_deg;
  bool has_distance;
  float distance_m;
  bool pick_allowed;
  bool target_confirmed;
} snu_robot_interfaces__msg__DetectedTarget;

// Struct for a sequence of snu_robot_interfaces__msg__DetectedTarget.
typedef struct snu_robot_interfaces__msg__DetectedTarget__Sequence
{
  snu_robot_interfaces__msg__DetectedTarget * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} snu_robot_interfaces__msg__DetectedTarget__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET__STRUCT_H_
