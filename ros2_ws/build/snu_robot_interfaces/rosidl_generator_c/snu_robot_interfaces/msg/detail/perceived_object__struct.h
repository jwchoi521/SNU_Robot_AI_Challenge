// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from snu_robot_interfaces:msg/PerceivedObject.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__PERCEIVED_OBJECT__STRUCT_H_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__PERCEIVED_OBJECT__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Constant 'ROLE_UNKNOWN'.
enum
{
  snu_robot_interfaces__msg__PerceivedObject__ROLE_UNKNOWN = 0
};

/// Constant 'ROLE_TARGET'.
enum
{
  snu_robot_interfaces__msg__PerceivedObject__ROLE_TARGET = 1
};

/// Constant 'ROLE_OBSTACLE'.
enum
{
  snu_robot_interfaces__msg__PerceivedObject__ROLE_OBSTACLE = 2
};

/// Constant 'ROLE_IGNORE'.
enum
{
  snu_robot_interfaces__msg__PerceivedObject__ROLE_IGNORE = 3
};

// Include directives for member types
// Member 'object_kind'
// Member 'fruit_kind'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/PerceivedObject in the package snu_robot_interfaces.
/**
  * One camera-visible object enriched with distance and navigation role.
  *
  * The detector should publish every relevant object, not only the current target.
  * Mission logic or perception post-processing assigns navigation_role:
  * target objects become approach goals, non-target objects become obstacles.
 */
typedef struct snu_robot_interfaces__msg__PerceivedObject
{
  rosidl_runtime_c__String object_kind;
  rosidl_runtime_c__String fruit_kind;
  uint8_t navigation_role;
  float confidence;
  float bbox_x1;
  float bbox_y1;
  float bbox_x2;
  float bbox_y2;
  /// Current YOLO convention: positive means image-right.
  float bearing_deg;
  bool has_distance;
  float distance_m;
  /// Optional physical radius used when expanding semantic obstacles.
  /// If this is 0, consumers use their configured default radius.
  float obstacle_radius_m;
  bool pick_allowed;
  bool target_confirmed;
} snu_robot_interfaces__msg__PerceivedObject;

// Struct for a sequence of snu_robot_interfaces__msg__PerceivedObject.
typedef struct snu_robot_interfaces__msg__PerceivedObject__Sequence
{
  snu_robot_interfaces__msg__PerceivedObject * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} snu_robot_interfaces__msg__PerceivedObject__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__PERCEIVED_OBJECT__STRUCT_H_
