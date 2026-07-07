// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from robot_object_detector_ros:msg/Detection2DArray.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__DETECTION2_D_ARRAY__STRUCT_H_
#define ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__DETECTION2_D_ARRAY__STRUCT_H_

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
// Member 'detections'
#include "robot_object_detector_ros/msg/detail/detection2_d__struct.h"

/// Struct defined in msg/Detection2DArray in the package robot_object_detector_ros.
typedef struct robot_object_detector_ros__msg__Detection2DArray
{
  std_msgs__msg__Header header;
  robot_object_detector_ros__msg__Detection2D__Sequence detections;
} robot_object_detector_ros__msg__Detection2DArray;

// Struct for a sequence of robot_object_detector_ros__msg__Detection2DArray.
typedef struct robot_object_detector_ros__msg__Detection2DArray__Sequence
{
  robot_object_detector_ros__msg__Detection2DArray * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} robot_object_detector_ros__msg__Detection2DArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__DETECTION2_D_ARRAY__STRUCT_H_
