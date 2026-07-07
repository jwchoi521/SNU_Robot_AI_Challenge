// generated from rosidl_typesupport_fastrtps_c/resource/idl__type_support_c.cpp.em
// with input from snu_robot_interfaces:msg/DetectedTarget.idl
// generated code does not contain a copyright notice
#include "snu_robot_interfaces/msg/detail/detected_target__rosidl_typesupport_fastrtps_c.h"


#include <cassert>
#include <limits>
#include <string>
#include "rosidl_typesupport_fastrtps_c/identifier.h"
#include "rosidl_typesupport_fastrtps_c/wstring_conversion.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "snu_robot_interfaces/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "snu_robot_interfaces/msg/detail/detected_target__struct.h"
#include "snu_robot_interfaces/msg/detail/detected_target__functions.h"
#include "fastcdr/Cdr.h"

#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-parameter"
# ifdef __clang__
#  pragma clang diagnostic ignored "-Wdeprecated-register"
#  pragma clang diagnostic ignored "-Wreturn-type-c-linkage"
# endif
#endif
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif

// includes and forward declarations of message dependencies and their conversion functions

#if defined(__cplusplus)
extern "C"
{
#endif

#include "rosidl_runtime_c/string.h"  // fruit_kind, object_kind
#include "rosidl_runtime_c/string_functions.h"  // fruit_kind, object_kind

// forward declare type support functions


using _DetectedTarget__ros_msg_type = snu_robot_interfaces__msg__DetectedTarget;

static bool _DetectedTarget__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  const _DetectedTarget__ros_msg_type * ros_message = static_cast<const _DetectedTarget__ros_msg_type *>(untyped_ros_message);
  // Field name: object_kind
  {
    const rosidl_runtime_c__String * str = &ros_message->object_kind;
    if (str->capacity == 0 || str->capacity <= str->size) {
      fprintf(stderr, "string capacity not greater than size\n");
      return false;
    }
    if (str->data[str->size] != '\0') {
      fprintf(stderr, "string not null-terminated\n");
      return false;
    }
    cdr << str->data;
  }

  // Field name: fruit_kind
  {
    const rosidl_runtime_c__String * str = &ros_message->fruit_kind;
    if (str->capacity == 0 || str->capacity <= str->size) {
      fprintf(stderr, "string capacity not greater than size\n");
      return false;
    }
    if (str->data[str->size] != '\0') {
      fprintf(stderr, "string not null-terminated\n");
      return false;
    }
    cdr << str->data;
  }

  // Field name: confidence
  {
    cdr << ros_message->confidence;
  }

  // Field name: bbox_x1
  {
    cdr << ros_message->bbox_x1;
  }

  // Field name: bbox_y1
  {
    cdr << ros_message->bbox_y1;
  }

  // Field name: bbox_x2
  {
    cdr << ros_message->bbox_x2;
  }

  // Field name: bbox_y2
  {
    cdr << ros_message->bbox_y2;
  }

  // Field name: bearing_deg
  {
    cdr << ros_message->bearing_deg;
  }

  // Field name: has_distance
  {
    cdr << (ros_message->has_distance ? true : false);
  }

  // Field name: distance_m
  {
    cdr << ros_message->distance_m;
  }

  // Field name: pick_allowed
  {
    cdr << (ros_message->pick_allowed ? true : false);
  }

  // Field name: target_confirmed
  {
    cdr << (ros_message->target_confirmed ? true : false);
  }

  return true;
}

static bool _DetectedTarget__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  _DetectedTarget__ros_msg_type * ros_message = static_cast<_DetectedTarget__ros_msg_type *>(untyped_ros_message);
  // Field name: object_kind
  {
    std::string tmp;
    cdr >> tmp;
    if (!ros_message->object_kind.data) {
      rosidl_runtime_c__String__init(&ros_message->object_kind);
    }
    bool succeeded = rosidl_runtime_c__String__assign(
      &ros_message->object_kind,
      tmp.c_str());
    if (!succeeded) {
      fprintf(stderr, "failed to assign string into field 'object_kind'\n");
      return false;
    }
  }

  // Field name: fruit_kind
  {
    std::string tmp;
    cdr >> tmp;
    if (!ros_message->fruit_kind.data) {
      rosidl_runtime_c__String__init(&ros_message->fruit_kind);
    }
    bool succeeded = rosidl_runtime_c__String__assign(
      &ros_message->fruit_kind,
      tmp.c_str());
    if (!succeeded) {
      fprintf(stderr, "failed to assign string into field 'fruit_kind'\n");
      return false;
    }
  }

  // Field name: confidence
  {
    cdr >> ros_message->confidence;
  }

  // Field name: bbox_x1
  {
    cdr >> ros_message->bbox_x1;
  }

  // Field name: bbox_y1
  {
    cdr >> ros_message->bbox_y1;
  }

  // Field name: bbox_x2
  {
    cdr >> ros_message->bbox_x2;
  }

  // Field name: bbox_y2
  {
    cdr >> ros_message->bbox_y2;
  }

  // Field name: bearing_deg
  {
    cdr >> ros_message->bearing_deg;
  }

  // Field name: has_distance
  {
    uint8_t tmp;
    cdr >> tmp;
    ros_message->has_distance = tmp ? true : false;
  }

  // Field name: distance_m
  {
    cdr >> ros_message->distance_m;
  }

  // Field name: pick_allowed
  {
    uint8_t tmp;
    cdr >> tmp;
    ros_message->pick_allowed = tmp ? true : false;
  }

  // Field name: target_confirmed
  {
    uint8_t tmp;
    cdr >> tmp;
    ros_message->target_confirmed = tmp ? true : false;
  }

  return true;
}  // NOLINT(readability/fn_size)

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_snu_robot_interfaces
size_t get_serialized_size_snu_robot_interfaces__msg__DetectedTarget(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _DetectedTarget__ros_msg_type * ros_message = static_cast<const _DetectedTarget__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // field.name object_kind
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message->object_kind.size + 1);
  // field.name fruit_kind
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message->fruit_kind.size + 1);
  // field.name confidence
  {
    size_t item_size = sizeof(ros_message->confidence);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name bbox_x1
  {
    size_t item_size = sizeof(ros_message->bbox_x1);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name bbox_y1
  {
    size_t item_size = sizeof(ros_message->bbox_y1);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name bbox_x2
  {
    size_t item_size = sizeof(ros_message->bbox_x2);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name bbox_y2
  {
    size_t item_size = sizeof(ros_message->bbox_y2);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name bearing_deg
  {
    size_t item_size = sizeof(ros_message->bearing_deg);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name has_distance
  {
    size_t item_size = sizeof(ros_message->has_distance);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name distance_m
  {
    size_t item_size = sizeof(ros_message->distance_m);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name pick_allowed
  {
    size_t item_size = sizeof(ros_message->pick_allowed);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name target_confirmed
  {
    size_t item_size = sizeof(ros_message->target_confirmed);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

static uint32_t _DetectedTarget__get_serialized_size(const void * untyped_ros_message)
{
  return static_cast<uint32_t>(
    get_serialized_size_snu_robot_interfaces__msg__DetectedTarget(
      untyped_ros_message, 0));
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_snu_robot_interfaces
size_t max_serialized_size_snu_robot_interfaces__msg__DetectedTarget(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;

  // member: object_kind
  {
    size_t array_size = 1;

    full_bounded = false;
    is_plain = false;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += padding +
        eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
        1;
    }
  }
  // member: fruit_kind
  {
    size_t array_size = 1;

    full_bounded = false;
    is_plain = false;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += padding +
        eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
        1;
    }
  }
  // member: confidence
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: bbox_x1
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: bbox_y1
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: bbox_x2
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: bbox_y2
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: bearing_deg
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: has_distance
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: distance_m
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: pick_allowed
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: target_confirmed
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = snu_robot_interfaces__msg__DetectedTarget;
    is_plain =
      (
      offsetof(DataType, target_confirmed) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}

static size_t _DetectedTarget__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_snu_robot_interfaces__msg__DetectedTarget(
    full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}


static message_type_support_callbacks_t __callbacks_DetectedTarget = {
  "snu_robot_interfaces::msg",
  "DetectedTarget",
  _DetectedTarget__cdr_serialize,
  _DetectedTarget__cdr_deserialize,
  _DetectedTarget__get_serialized_size,
  _DetectedTarget__max_serialized_size
};

static rosidl_message_type_support_t _DetectedTarget__type_support = {
  rosidl_typesupport_fastrtps_c__identifier,
  &__callbacks_DetectedTarget,
  get_message_typesupport_handle_function,
};

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, snu_robot_interfaces, msg, DetectedTarget)() {
  return &_DetectedTarget__type_support;
}

#if defined(__cplusplus)
}
#endif
