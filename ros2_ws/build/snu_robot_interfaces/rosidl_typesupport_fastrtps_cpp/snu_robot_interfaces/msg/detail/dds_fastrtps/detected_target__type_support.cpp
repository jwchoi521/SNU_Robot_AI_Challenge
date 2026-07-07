// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__type_support.cpp.em
// with input from snu_robot_interfaces:msg/DetectedTarget.idl
// generated code does not contain a copyright notice
#include "snu_robot_interfaces/msg/detail/detected_target__rosidl_typesupport_fastrtps_cpp.hpp"
#include "snu_robot_interfaces/msg/detail/detected_target__struct.hpp"

#include <limits>
#include <stdexcept>
#include <string>
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_fastrtps_cpp/identifier.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_fastrtps_cpp/wstring_conversion.hpp"
#include "fastcdr/Cdr.h"


// forward declaration of message dependencies and their conversion functions

namespace snu_robot_interfaces
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_snu_robot_interfaces
cdr_serialize(
  const snu_robot_interfaces::msg::DetectedTarget & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: object_kind
  cdr << ros_message.object_kind;
  // Member: fruit_kind
  cdr << ros_message.fruit_kind;
  // Member: confidence
  cdr << ros_message.confidence;
  // Member: bbox_x1
  cdr << ros_message.bbox_x1;
  // Member: bbox_y1
  cdr << ros_message.bbox_y1;
  // Member: bbox_x2
  cdr << ros_message.bbox_x2;
  // Member: bbox_y2
  cdr << ros_message.bbox_y2;
  // Member: bearing_deg
  cdr << ros_message.bearing_deg;
  // Member: has_distance
  cdr << (ros_message.has_distance ? true : false);
  // Member: distance_m
  cdr << ros_message.distance_m;
  // Member: pick_allowed
  cdr << (ros_message.pick_allowed ? true : false);
  // Member: target_confirmed
  cdr << (ros_message.target_confirmed ? true : false);
  return true;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_snu_robot_interfaces
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  snu_robot_interfaces::msg::DetectedTarget & ros_message)
{
  // Member: object_kind
  cdr >> ros_message.object_kind;

  // Member: fruit_kind
  cdr >> ros_message.fruit_kind;

  // Member: confidence
  cdr >> ros_message.confidence;

  // Member: bbox_x1
  cdr >> ros_message.bbox_x1;

  // Member: bbox_y1
  cdr >> ros_message.bbox_y1;

  // Member: bbox_x2
  cdr >> ros_message.bbox_x2;

  // Member: bbox_y2
  cdr >> ros_message.bbox_y2;

  // Member: bearing_deg
  cdr >> ros_message.bearing_deg;

  // Member: has_distance
  {
    uint8_t tmp;
    cdr >> tmp;
    ros_message.has_distance = tmp ? true : false;
  }

  // Member: distance_m
  cdr >> ros_message.distance_m;

  // Member: pick_allowed
  {
    uint8_t tmp;
    cdr >> tmp;
    ros_message.pick_allowed = tmp ? true : false;
  }

  // Member: target_confirmed
  {
    uint8_t tmp;
    cdr >> tmp;
    ros_message.target_confirmed = tmp ? true : false;
  }

  return true;
}  // NOLINT(readability/fn_size)

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_snu_robot_interfaces
get_serialized_size(
  const snu_robot_interfaces::msg::DetectedTarget & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: object_kind
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message.object_kind.size() + 1);
  // Member: fruit_kind
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message.fruit_kind.size() + 1);
  // Member: confidence
  {
    size_t item_size = sizeof(ros_message.confidence);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: bbox_x1
  {
    size_t item_size = sizeof(ros_message.bbox_x1);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: bbox_y1
  {
    size_t item_size = sizeof(ros_message.bbox_y1);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: bbox_x2
  {
    size_t item_size = sizeof(ros_message.bbox_x2);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: bbox_y2
  {
    size_t item_size = sizeof(ros_message.bbox_y2);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: bearing_deg
  {
    size_t item_size = sizeof(ros_message.bearing_deg);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: has_distance
  {
    size_t item_size = sizeof(ros_message.has_distance);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: distance_m
  {
    size_t item_size = sizeof(ros_message.distance_m);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: pick_allowed
  {
    size_t item_size = sizeof(ros_message.pick_allowed);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: target_confirmed
  {
    size_t item_size = sizeof(ros_message.target_confirmed);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_snu_robot_interfaces
max_serialized_size_DetectedTarget(
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


  // Member: object_kind
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

  // Member: fruit_kind
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

  // Member: confidence
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Member: bbox_x1
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Member: bbox_y1
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Member: bbox_x2
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Member: bbox_y2
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Member: bearing_deg
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Member: has_distance
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: distance_m
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Member: pick_allowed
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: target_confirmed
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
    using DataType = snu_robot_interfaces::msg::DetectedTarget;
    is_plain =
      (
      offsetof(DataType, target_confirmed) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}

static bool _DetectedTarget__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  auto typed_message =
    static_cast<const snu_robot_interfaces::msg::DetectedTarget *>(
    untyped_ros_message);
  return cdr_serialize(*typed_message, cdr);
}

static bool _DetectedTarget__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  auto typed_message =
    static_cast<snu_robot_interfaces::msg::DetectedTarget *>(
    untyped_ros_message);
  return cdr_deserialize(cdr, *typed_message);
}

static uint32_t _DetectedTarget__get_serialized_size(
  const void * untyped_ros_message)
{
  auto typed_message =
    static_cast<const snu_robot_interfaces::msg::DetectedTarget *>(
    untyped_ros_message);
  return static_cast<uint32_t>(get_serialized_size(*typed_message, 0));
}

static size_t _DetectedTarget__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_DetectedTarget(full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}

static message_type_support_callbacks_t _DetectedTarget__callbacks = {
  "snu_robot_interfaces::msg",
  "DetectedTarget",
  _DetectedTarget__cdr_serialize,
  _DetectedTarget__cdr_deserialize,
  _DetectedTarget__get_serialized_size,
  _DetectedTarget__max_serialized_size
};

static rosidl_message_type_support_t _DetectedTarget__handle = {
  rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
  &_DetectedTarget__callbacks,
  get_message_typesupport_handle_function,
};

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace snu_robot_interfaces

namespace rosidl_typesupport_fastrtps_cpp
{

template<>
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_EXPORT_snu_robot_interfaces
const rosidl_message_type_support_t *
get_message_type_support_handle<snu_robot_interfaces::msg::DetectedTarget>()
{
  return &snu_robot_interfaces::msg::typesupport_fastrtps_cpp::_DetectedTarget__handle;
}

}  // namespace rosidl_typesupport_fastrtps_cpp

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, snu_robot_interfaces, msg, DetectedTarget)() {
  return &snu_robot_interfaces::msg::typesupport_fastrtps_cpp::_DetectedTarget__handle;
}

#ifdef __cplusplus
}
#endif
