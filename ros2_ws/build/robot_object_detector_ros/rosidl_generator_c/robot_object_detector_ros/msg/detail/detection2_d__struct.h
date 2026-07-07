// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from robot_object_detector_ros:msg/Detection2D.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__DETECTION2_D__STRUCT_H_
#define ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__DETECTION2_D__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'class_name'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/Detection2D in the package robot_object_detector_ros.
typedef struct robot_object_detector_ros__msg__Detection2D
{
  int32_t class_id;
  rosidl_runtime_c__String class_name;
  float confidence;
  float x1;
  float y1;
  float x2;
  float y2;
} robot_object_detector_ros__msg__Detection2D;

// Struct for a sequence of robot_object_detector_ros__msg__Detection2D.
typedef struct robot_object_detector_ros__msg__Detection2D__Sequence
{
  robot_object_detector_ros__msg__Detection2D * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} robot_object_detector_ros__msg__Detection2D__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__DETECTION2_D__STRUCT_H_
