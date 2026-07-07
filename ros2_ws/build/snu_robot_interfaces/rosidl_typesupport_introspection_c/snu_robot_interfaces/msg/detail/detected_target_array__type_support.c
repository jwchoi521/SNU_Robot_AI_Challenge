// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from snu_robot_interfaces:msg/DetectedTargetArray.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "snu_robot_interfaces/msg/detail/detected_target_array__rosidl_typesupport_introspection_c.h"
#include "snu_robot_interfaces/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "snu_robot_interfaces/msg/detail/detected_target_array__functions.h"
#include "snu_robot_interfaces/msg/detail/detected_target_array__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `targets`
#include "snu_robot_interfaces/msg/detected_target.h"
// Member `targets`
#include "snu_robot_interfaces/msg/detail/detected_target__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__DetectedTargetArray_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  snu_robot_interfaces__msg__DetectedTargetArray__init(message_memory);
}

void snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__DetectedTargetArray_fini_function(void * message_memory)
{
  snu_robot_interfaces__msg__DetectedTargetArray__fini(message_memory);
}

size_t snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__size_function__DetectedTargetArray__targets(
  const void * untyped_member)
{
  const snu_robot_interfaces__msg__DetectedTarget__Sequence * member =
    (const snu_robot_interfaces__msg__DetectedTarget__Sequence *)(untyped_member);
  return member->size;
}

const void * snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__get_const_function__DetectedTargetArray__targets(
  const void * untyped_member, size_t index)
{
  const snu_robot_interfaces__msg__DetectedTarget__Sequence * member =
    (const snu_robot_interfaces__msg__DetectedTarget__Sequence *)(untyped_member);
  return &member->data[index];
}

void * snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__get_function__DetectedTargetArray__targets(
  void * untyped_member, size_t index)
{
  snu_robot_interfaces__msg__DetectedTarget__Sequence * member =
    (snu_robot_interfaces__msg__DetectedTarget__Sequence *)(untyped_member);
  return &member->data[index];
}

void snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__fetch_function__DetectedTargetArray__targets(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const snu_robot_interfaces__msg__DetectedTarget * item =
    ((const snu_robot_interfaces__msg__DetectedTarget *)
    snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__get_const_function__DetectedTargetArray__targets(untyped_member, index));
  snu_robot_interfaces__msg__DetectedTarget * value =
    (snu_robot_interfaces__msg__DetectedTarget *)(untyped_value);
  *value = *item;
}

void snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__assign_function__DetectedTargetArray__targets(
  void * untyped_member, size_t index, const void * untyped_value)
{
  snu_robot_interfaces__msg__DetectedTarget * item =
    ((snu_robot_interfaces__msg__DetectedTarget *)
    snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__get_function__DetectedTargetArray__targets(untyped_member, index));
  const snu_robot_interfaces__msg__DetectedTarget * value =
    (const snu_robot_interfaces__msg__DetectedTarget *)(untyped_value);
  *item = *value;
}

bool snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__resize_function__DetectedTargetArray__targets(
  void * untyped_member, size_t size)
{
  snu_robot_interfaces__msg__DetectedTarget__Sequence * member =
    (snu_robot_interfaces__msg__DetectedTarget__Sequence *)(untyped_member);
  snu_robot_interfaces__msg__DetectedTarget__Sequence__fini(member);
  return snu_robot_interfaces__msg__DetectedTarget__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__DetectedTargetArray_message_member_array[2] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(snu_robot_interfaces__msg__DetectedTargetArray, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "targets",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(snu_robot_interfaces__msg__DetectedTargetArray, targets),  // bytes offset in struct
    NULL,  // default value
    snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__size_function__DetectedTargetArray__targets,  // size() function pointer
    snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__get_const_function__DetectedTargetArray__targets,  // get_const(index) function pointer
    snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__get_function__DetectedTargetArray__targets,  // get(index) function pointer
    snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__fetch_function__DetectedTargetArray__targets,  // fetch(index, &value) function pointer
    snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__assign_function__DetectedTargetArray__targets,  // assign(index, value) function pointer
    snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__resize_function__DetectedTargetArray__targets  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__DetectedTargetArray_message_members = {
  "snu_robot_interfaces__msg",  // message namespace
  "DetectedTargetArray",  // message name
  2,  // number of fields
  sizeof(snu_robot_interfaces__msg__DetectedTargetArray),
  snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__DetectedTargetArray_message_member_array,  // message members
  snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__DetectedTargetArray_init_function,  // function to initialize message memory (memory has to be allocated)
  snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__DetectedTargetArray_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__DetectedTargetArray_message_type_support_handle = {
  0,
  &snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__DetectedTargetArray_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_snu_robot_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, snu_robot_interfaces, msg, DetectedTargetArray)() {
  snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__DetectedTargetArray_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__DetectedTargetArray_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, snu_robot_interfaces, msg, DetectedTarget)();
  if (!snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__DetectedTargetArray_message_type_support_handle.typesupport_identifier) {
    snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__DetectedTargetArray_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &snu_robot_interfaces__msg__DetectedTargetArray__rosidl_typesupport_introspection_c__DetectedTargetArray_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
