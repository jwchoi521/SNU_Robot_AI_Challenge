// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__type_support.cpp.em
// with input from robot_object_detector_ros:msg/FruitClassification.idl
// generated code does not contain a copyright notice
#include "robot_object_detector_ros/msg/detail/fruit_classification__rosidl_typesupport_fastrtps_cpp.hpp"
#include "robot_object_detector_ros/msg/detail/fruit_classification__struct.hpp"

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
namespace robot_object_detector_ros
{
namespace msg
{
namespace typesupport_fastrtps_cpp
{
bool cdr_serialize(
  const robot_object_detector_ros::msg::Detection2D &,
  eprosima::fastcdr::Cdr &);
bool cdr_deserialize(
  eprosima::fastcdr::Cdr &,
  robot_object_detector_ros::msg::Detection2D &);
size_t get_serialized_size(
  const robot_object_detector_ros::msg::Detection2D &,
  size_t current_alignment);
size_t
max_serialized_size_Detection2D(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);
}  // namespace typesupport_fastrtps_cpp
}  // namespace msg
}  // namespace robot_object_detector_ros


namespace robot_object_detector_ros
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_robot_object_detector_ros
cdr_serialize(
  const robot_object_detector_ros::msg::FruitClassification & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: cube
  robot_object_detector_ros::msg::typesupport_fastrtps_cpp::cdr_serialize(
    ros_message.cube,
    cdr);
  // Member: fruit_kind
  cdr << ros_message.fruit_kind;
  // Member: confidence
  cdr << ros_message.confidence;
  // Member: pick_allowed
  cdr << (ros_message.pick_allowed ? true : false);
  // Member: class_names
  {
    cdr << ros_message.class_names;
  }
  // Member: probabilities
  {
    cdr << ros_message.probabilities;
  }
  return true;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_robot_object_detector_ros
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  robot_object_detector_ros::msg::FruitClassification & ros_message)
{
  // Member: cube
  robot_object_detector_ros::msg::typesupport_fastrtps_cpp::cdr_deserialize(
    cdr, ros_message.cube);

  // Member: fruit_kind
  cdr >> ros_message.fruit_kind;

  // Member: confidence
  cdr >> ros_message.confidence;

  // Member: pick_allowed
  {
    uint8_t tmp;
    cdr >> tmp;
    ros_message.pick_allowed = tmp ? true : false;
  }

  // Member: class_names
  {
    cdr >> ros_message.class_names;
  }

  // Member: probabilities
  {
    cdr >> ros_message.probabilities;
  }

  return true;
}  // NOLINT(readability/fn_size)

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_robot_object_detector_ros
get_serialized_size(
  const robot_object_detector_ros::msg::FruitClassification & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: cube

  current_alignment +=
    robot_object_detector_ros::msg::typesupport_fastrtps_cpp::get_serialized_size(
    ros_message.cube, current_alignment);
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
  // Member: pick_allowed
  {
    size_t item_size = sizeof(ros_message.pick_allowed);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: class_names
  {
    size_t array_size = ros_message.class_names.size();

    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += padding +
        eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
        (ros_message.class_names[index].size() + 1);
    }
  }
  // Member: probabilities
  {
    size_t array_size = ros_message.probabilities.size();

    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    size_t item_size = sizeof(ros_message.probabilities[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_robot_object_detector_ros
max_serialized_size_FruitClassification(
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


  // Member: cube
  {
    size_t array_size = 1;


    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size =
        robot_object_detector_ros::msg::typesupport_fastrtps_cpp::max_serialized_size_Detection2D(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
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

  // Member: pick_allowed
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: class_names
  {
    size_t array_size = 0;
    full_bounded = false;
    is_plain = false;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);

    full_bounded = false;
    is_plain = false;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += padding +
        eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
        1;
    }
  }

  // Member: probabilities
  {
    size_t array_size = 0;
    full_bounded = false;
    is_plain = false;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = robot_object_detector_ros::msg::FruitClassification;
    is_plain =
      (
      offsetof(DataType, probabilities) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}

static bool _FruitClassification__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  auto typed_message =
    static_cast<const robot_object_detector_ros::msg::FruitClassification *>(
    untyped_ros_message);
  return cdr_serialize(*typed_message, cdr);
}

static bool _FruitClassification__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  auto typed_message =
    static_cast<robot_object_detector_ros::msg::FruitClassification *>(
    untyped_ros_message);
  return cdr_deserialize(cdr, *typed_message);
}

static uint32_t _FruitClassification__get_serialized_size(
  const void * untyped_ros_message)
{
  auto typed_message =
    static_cast<const robot_object_detector_ros::msg::FruitClassification *>(
    untyped_ros_message);
  return static_cast<uint32_t>(get_serialized_size(*typed_message, 0));
}

static size_t _FruitClassification__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_FruitClassification(full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}

static message_type_support_callbacks_t _FruitClassification__callbacks = {
  "robot_object_detector_ros::msg",
  "FruitClassification",
  _FruitClassification__cdr_serialize,
  _FruitClassification__cdr_deserialize,
  _FruitClassification__get_serialized_size,
  _FruitClassification__max_serialized_size
};

static rosidl_message_type_support_t _FruitClassification__handle = {
  rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
  &_FruitClassification__callbacks,
  get_message_typesupport_handle_function,
};

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace robot_object_detector_ros

namespace rosidl_typesupport_fastrtps_cpp
{

template<>
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_EXPORT_robot_object_detector_ros
const rosidl_message_type_support_t *
get_message_type_support_handle<robot_object_detector_ros::msg::FruitClassification>()
{
  return &robot_object_detector_ros::msg::typesupport_fastrtps_cpp::_FruitClassification__handle;
}

}  // namespace rosidl_typesupport_fastrtps_cpp

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, robot_object_detector_ros, msg, FruitClassification)() {
  return &robot_object_detector_ros::msg::typesupport_fastrtps_cpp::_FruitClassification__handle;
}

#ifdef __cplusplus
}
#endif
