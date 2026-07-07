// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from snu_robot_interfaces:msg/FourWheelCommand.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "snu_robot_interfaces/msg/detail/four_wheel_command__rosidl_typesupport_introspection_c.h"
#include "snu_robot_interfaces/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "snu_robot_interfaces/msg/detail/four_wheel_command__functions.h"
#include "snu_robot_interfaces/msg/detail/four_wheel_command__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void snu_robot_interfaces__msg__FourWheelCommand__rosidl_typesupport_introspection_c__FourWheelCommand_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  snu_robot_interfaces__msg__FourWheelCommand__init(message_memory);
}

void snu_robot_interfaces__msg__FourWheelCommand__rosidl_typesupport_introspection_c__FourWheelCommand_fini_function(void * message_memory)
{
  snu_robot_interfaces__msg__FourWheelCommand__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember snu_robot_interfaces__msg__FourWheelCommand__rosidl_typesupport_introspection_c__FourWheelCommand_message_member_array[6] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(snu_robot_interfaces__msg__FourWheelCommand, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "command_mode",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(snu_robot_interfaces__msg__FourWheelCommand, command_mode),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "front_left",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(snu_robot_interfaces__msg__FourWheelCommand, front_left),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "front_right",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(snu_robot_interfaces__msg__FourWheelCommand, front_right),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "rear_left",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(snu_robot_interfaces__msg__FourWheelCommand, rear_left),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "rear_right",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(snu_robot_interfaces__msg__FourWheelCommand, rear_right),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers snu_robot_interfaces__msg__FourWheelCommand__rosidl_typesupport_introspection_c__FourWheelCommand_message_members = {
  "snu_robot_interfaces__msg",  // message namespace
  "FourWheelCommand",  // message name
  6,  // number of fields
  sizeof(snu_robot_interfaces__msg__FourWheelCommand),
  snu_robot_interfaces__msg__FourWheelCommand__rosidl_typesupport_introspection_c__FourWheelCommand_message_member_array,  // message members
  snu_robot_interfaces__msg__FourWheelCommand__rosidl_typesupport_introspection_c__FourWheelCommand_init_function,  // function to initialize message memory (memory has to be allocated)
  snu_robot_interfaces__msg__FourWheelCommand__rosidl_typesupport_introspection_c__FourWheelCommand_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t snu_robot_interfaces__msg__FourWheelCommand__rosidl_typesupport_introspection_c__FourWheelCommand_message_type_support_handle = {
  0,
  &snu_robot_interfaces__msg__FourWheelCommand__rosidl_typesupport_introspection_c__FourWheelCommand_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_snu_robot_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, snu_robot_interfaces, msg, FourWheelCommand)() {
  snu_robot_interfaces__msg__FourWheelCommand__rosidl_typesupport_introspection_c__FourWheelCommand_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  if (!snu_robot_interfaces__msg__FourWheelCommand__rosidl_typesupport_introspection_c__FourWheelCommand_message_type_support_handle.typesupport_identifier) {
    snu_robot_interfaces__msg__FourWheelCommand__rosidl_typesupport_introspection_c__FourWheelCommand_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &snu_robot_interfaces__msg__FourWheelCommand__rosidl_typesupport_introspection_c__FourWheelCommand_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
