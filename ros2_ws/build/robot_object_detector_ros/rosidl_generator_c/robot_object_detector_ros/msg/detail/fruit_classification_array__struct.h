// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from robot_object_detector_ros:msg/FruitClassificationArray.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION_ARRAY__STRUCT_H_
#define ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION_ARRAY__STRUCT_H_

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
// Member 'classifications'
#include "robot_object_detector_ros/msg/detail/fruit_classification__struct.h"

/// Struct defined in msg/FruitClassificationArray in the package robot_object_detector_ros.
typedef struct robot_object_detector_ros__msg__FruitClassificationArray
{
  std_msgs__msg__Header header;
  robot_object_detector_ros__msg__FruitClassification__Sequence classifications;
} robot_object_detector_ros__msg__FruitClassificationArray;

// Struct for a sequence of robot_object_detector_ros__msg__FruitClassificationArray.
typedef struct robot_object_detector_ros__msg__FruitClassificationArray__Sequence
{
  robot_object_detector_ros__msg__FruitClassificationArray * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} robot_object_detector_ros__msg__FruitClassificationArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION_ARRAY__STRUCT_H_
