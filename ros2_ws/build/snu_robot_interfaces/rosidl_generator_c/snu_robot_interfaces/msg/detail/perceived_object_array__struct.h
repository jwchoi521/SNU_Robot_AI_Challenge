// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from snu_robot_interfaces:msg/PerceivedObjectArray.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__PERCEIVED_OBJECT_ARRAY__STRUCT_H_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__PERCEIVED_OBJECT_ARRAY__STRUCT_H_

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
// Member 'objects'
#include "snu_robot_interfaces/msg/detail/perceived_object__struct.h"

/// Struct defined in msg/PerceivedObjectArray in the package snu_robot_interfaces.
typedef struct snu_robot_interfaces__msg__PerceivedObjectArray
{
  std_msgs__msg__Header header;
  snu_robot_interfaces__msg__PerceivedObject__Sequence objects;
} snu_robot_interfaces__msg__PerceivedObjectArray;

// Struct for a sequence of snu_robot_interfaces__msg__PerceivedObjectArray.
typedef struct snu_robot_interfaces__msg__PerceivedObjectArray__Sequence
{
  snu_robot_interfaces__msg__PerceivedObjectArray * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} snu_robot_interfaces__msg__PerceivedObjectArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__PERCEIVED_OBJECT_ARRAY__STRUCT_H_
