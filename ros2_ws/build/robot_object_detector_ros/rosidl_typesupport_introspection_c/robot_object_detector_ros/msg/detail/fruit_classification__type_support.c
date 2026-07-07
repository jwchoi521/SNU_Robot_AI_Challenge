// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from robot_object_detector_ros:msg/FruitClassification.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "robot_object_detector_ros/msg/detail/fruit_classification__rosidl_typesupport_introspection_c.h"
#include "robot_object_detector_ros/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "robot_object_detector_ros/msg/detail/fruit_classification__functions.h"
#include "robot_object_detector_ros/msg/detail/fruit_classification__struct.h"


// Include directives for member types
// Member `cube`
#include "robot_object_detector_ros/msg/detection2_d.h"
// Member `cube`
#include "robot_object_detector_ros/msg/detail/detection2_d__rosidl_typesupport_introspection_c.h"
// Member `fruit_kind`
// Member `class_names`
#include "rosidl_runtime_c/string_functions.h"
// Member `probabilities`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__FruitClassification_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  robot_object_detector_ros__msg__FruitClassification__init(message_memory);
}

void robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__FruitClassification_fini_function(void * message_memory)
{
  robot_object_detector_ros__msg__FruitClassification__fini(message_memory);
}

size_t robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__size_function__FruitClassification__class_names(
  const void * untyped_member)
{
  const rosidl_runtime_c__String__Sequence * member =
    (const rosidl_runtime_c__String__Sequence *)(untyped_member);
  return member->size;
}

const void * robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__get_const_function__FruitClassification__class_names(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__String__Sequence * member =
    (const rosidl_runtime_c__String__Sequence *)(untyped_member);
  return &member->data[index];
}

void * robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__get_function__FruitClassification__class_names(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__String__Sequence * member =
    (rosidl_runtime_c__String__Sequence *)(untyped_member);
  return &member->data[index];
}

void robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__fetch_function__FruitClassification__class_names(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const rosidl_runtime_c__String * item =
    ((const rosidl_runtime_c__String *)
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__get_const_function__FruitClassification__class_names(untyped_member, index));
  rosidl_runtime_c__String * value =
    (rosidl_runtime_c__String *)(untyped_value);
  *value = *item;
}

void robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__assign_function__FruitClassification__class_names(
  void * untyped_member, size_t index, const void * untyped_value)
{
  rosidl_runtime_c__String * item =
    ((rosidl_runtime_c__String *)
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__get_function__FruitClassification__class_names(untyped_member, index));
  const rosidl_runtime_c__String * value =
    (const rosidl_runtime_c__String *)(untyped_value);
  *item = *value;
}

bool robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__resize_function__FruitClassification__class_names(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__String__Sequence * member =
    (rosidl_runtime_c__String__Sequence *)(untyped_member);
  rosidl_runtime_c__String__Sequence__fini(member);
  return rosidl_runtime_c__String__Sequence__init(member, size);
}

size_t robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__size_function__FruitClassification__probabilities(
  const void * untyped_member)
{
  const rosidl_runtime_c__float__Sequence * member =
    (const rosidl_runtime_c__float__Sequence *)(untyped_member);
  return member->size;
}

const void * robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__get_const_function__FruitClassification__probabilities(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__float__Sequence * member =
    (const rosidl_runtime_c__float__Sequence *)(untyped_member);
  return &member->data[index];
}

void * robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__get_function__FruitClassification__probabilities(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__float__Sequence * member =
    (rosidl_runtime_c__float__Sequence *)(untyped_member);
  return &member->data[index];
}

void robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__fetch_function__FruitClassification__probabilities(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const float * item =
    ((const float *)
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__get_const_function__FruitClassification__probabilities(untyped_member, index));
  float * value =
    (float *)(untyped_value);
  *value = *item;
}

void robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__assign_function__FruitClassification__probabilities(
  void * untyped_member, size_t index, const void * untyped_value)
{
  float * item =
    ((float *)
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__get_function__FruitClassification__probabilities(untyped_member, index));
  const float * value =
    (const float *)(untyped_value);
  *item = *value;
}

bool robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__resize_function__FruitClassification__probabilities(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__float__Sequence * member =
    (rosidl_runtime_c__float__Sequence *)(untyped_member);
  rosidl_runtime_c__float__Sequence__fini(member);
  return rosidl_runtime_c__float__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__FruitClassification_message_member_array[6] = {
  {
    "cube",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_object_detector_ros__msg__FruitClassification, cube),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "fruit_kind",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_object_detector_ros__msg__FruitClassification, fruit_kind),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "confidence",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_object_detector_ros__msg__FruitClassification, confidence),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "pick_allowed",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_object_detector_ros__msg__FruitClassification, pick_allowed),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "class_names",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_object_detector_ros__msg__FruitClassification, class_names),  // bytes offset in struct
    NULL,  // default value
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__size_function__FruitClassification__class_names,  // size() function pointer
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__get_const_function__FruitClassification__class_names,  // get_const(index) function pointer
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__get_function__FruitClassification__class_names,  // get(index) function pointer
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__fetch_function__FruitClassification__class_names,  // fetch(index, &value) function pointer
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__assign_function__FruitClassification__class_names,  // assign(index, value) function pointer
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__resize_function__FruitClassification__class_names  // resize(index) function pointer
  },
  {
    "probabilities",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_object_detector_ros__msg__FruitClassification, probabilities),  // bytes offset in struct
    NULL,  // default value
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__size_function__FruitClassification__probabilities,  // size() function pointer
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__get_const_function__FruitClassification__probabilities,  // get_const(index) function pointer
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__get_function__FruitClassification__probabilities,  // get(index) function pointer
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__fetch_function__FruitClassification__probabilities,  // fetch(index, &value) function pointer
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__assign_function__FruitClassification__probabilities,  // assign(index, value) function pointer
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__resize_function__FruitClassification__probabilities  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__FruitClassification_message_members = {
  "robot_object_detector_ros__msg",  // message namespace
  "FruitClassification",  // message name
  6,  // number of fields
  sizeof(robot_object_detector_ros__msg__FruitClassification),
  robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__FruitClassification_message_member_array,  // message members
  robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__FruitClassification_init_function,  // function to initialize message memory (memory has to be allocated)
  robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__FruitClassification_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__FruitClassification_message_type_support_handle = {
  0,
  &robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__FruitClassification_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_robot_object_detector_ros
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, robot_object_detector_ros, msg, FruitClassification)() {
  robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__FruitClassification_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, robot_object_detector_ros, msg, Detection2D)();
  if (!robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__FruitClassification_message_type_support_handle.typesupport_identifier) {
    robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__FruitClassification_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &robot_object_detector_ros__msg__FruitClassification__rosidl_typesupport_introspection_c__FruitClassification_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
