// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from robot_object_detector_ros:msg/FruitClassification.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION__STRUCT_H_
#define ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'cube'
#include "robot_object_detector_ros/msg/detail/detection2_d__struct.h"
// Member 'fruit_kind'
// Member 'class_names'
#include "rosidl_runtime_c/string.h"
// Member 'probabilities'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in msg/FruitClassification in the package robot_object_detector_ros.
typedef struct robot_object_detector_ros__msg__FruitClassification
{
  robot_object_detector_ros__msg__Detection2D cube;
  rosidl_runtime_c__String fruit_kind;
  float confidence;
  bool pick_allowed;
  rosidl_runtime_c__String__Sequence class_names;
  rosidl_runtime_c__float__Sequence probabilities;
} robot_object_detector_ros__msg__FruitClassification;

// Struct for a sequence of robot_object_detector_ros__msg__FruitClassification.
typedef struct robot_object_detector_ros__msg__FruitClassification__Sequence
{
  robot_object_detector_ros__msg__FruitClassification * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} robot_object_detector_ros__msg__FruitClassification__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION__STRUCT_H_
