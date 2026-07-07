// generated from rosidl_typesupport_fastrtps_c/resource/idl__type_support_c.cpp.em
// with input from robot_object_detector_ros:msg/FruitClassification.idl
// generated code does not contain a copyright notice
#include "robot_object_detector_ros/msg/detail/fruit_classification__rosidl_typesupport_fastrtps_c.h"


#include <cassert>
#include <limits>
#include <string>
#include "rosidl_typesupport_fastrtps_c/identifier.h"
#include "rosidl_typesupport_fastrtps_c/wstring_conversion.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "robot_object_detector_ros/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "robot_object_detector_ros/msg/detail/fruit_classification__struct.h"
#include "robot_object_detector_ros/msg/detail/fruit_classification__functions.h"
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

#include "robot_object_detector_ros/msg/detail/detection2_d__functions.h"  // cube
#include "rosidl_runtime_c/primitives_sequence.h"  // probabilities
#include "rosidl_runtime_c/primitives_sequence_functions.h"  // probabilities
#include "rosidl_runtime_c/string.h"  // class_names, fruit_kind
#include "rosidl_runtime_c/string_functions.h"  // class_names, fruit_kind

// forward declare type support functions
size_t get_serialized_size_robot_object_detector_ros__msg__Detection2D(
  const void * untyped_ros_message,
  size_t current_alignment);

size_t max_serialized_size_robot_object_detector_ros__msg__Detection2D(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

const rosidl_message_type_support_t *
  ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, robot_object_detector_ros, msg, Detection2D)();


using _FruitClassification__ros_msg_type = robot_object_detector_ros__msg__FruitClassification;

static bool _FruitClassification__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  const _FruitClassification__ros_msg_type * ros_message = static_cast<const _FruitClassification__ros_msg_type *>(untyped_ros_message);
  // Field name: cube
  {
    const message_type_support_callbacks_t * callbacks =
      static_cast<const message_type_support_callbacks_t *>(
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
        rosidl_typesupport_fastrtps_c, robot_object_detector_ros, msg, Detection2D
      )()->data);
    if (!callbacks->cdr_serialize(
        &ros_message->cube, cdr))
    {
      return false;
    }
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

  // Field name: pick_allowed
  {
    cdr << (ros_message->pick_allowed ? true : false);
  }

  // Field name: class_names
  {
    size_t size = ros_message->class_names.size;
    auto array_ptr = ros_message->class_names.data;
    cdr << static_cast<uint32_t>(size);
    for (size_t i = 0; i < size; ++i) {
      const rosidl_runtime_c__String * str = &array_ptr[i];
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
  }

  // Field name: probabilities
  {
    size_t size = ros_message->probabilities.size;
    auto array_ptr = ros_message->probabilities.data;
    cdr << static_cast<uint32_t>(size);
    cdr.serializeArray(array_ptr, size);
  }

  return true;
}

static bool _FruitClassification__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  _FruitClassification__ros_msg_type * ros_message = static_cast<_FruitClassification__ros_msg_type *>(untyped_ros_message);
  // Field name: cube
  {
    const message_type_support_callbacks_t * callbacks =
      static_cast<const message_type_support_callbacks_t *>(
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
        rosidl_typesupport_fastrtps_c, robot_object_detector_ros, msg, Detection2D
      )()->data);
    if (!callbacks->cdr_deserialize(
        cdr, &ros_message->cube))
    {
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

  // Field name: pick_allowed
  {
    uint8_t tmp;
    cdr >> tmp;
    ros_message->pick_allowed = tmp ? true : false;
  }

  // Field name: class_names
  {
    uint32_t cdrSize;
    cdr >> cdrSize;
    size_t size = static_cast<size_t>(cdrSize);

    // Check there are at least 'size' remaining bytes in the CDR stream before resizing
    auto old_state = cdr.getState();
    bool correct_size = cdr.jump(size);
    cdr.setState(old_state);
    if (!correct_size) {
      fprintf(stderr, "sequence size exceeds remaining buffer\n");
      return false;
    }

    if (ros_message->class_names.data) {
      rosidl_runtime_c__String__Sequence__fini(&ros_message->class_names);
    }
    if (!rosidl_runtime_c__String__Sequence__init(&ros_message->class_names, size)) {
      fprintf(stderr, "failed to create array for field 'class_names'");
      return false;
    }
    auto array_ptr = ros_message->class_names.data;
    for (size_t i = 0; i < size; ++i) {
      std::string tmp;
      cdr >> tmp;
      auto & ros_i = array_ptr[i];
      if (!ros_i.data) {
        rosidl_runtime_c__String__init(&ros_i);
      }
      bool succeeded = rosidl_runtime_c__String__assign(
        &ros_i,
        tmp.c_str());
      if (!succeeded) {
        fprintf(stderr, "failed to assign string into field 'class_names'\n");
        return false;
      }
    }
  }

  // Field name: probabilities
  {
    uint32_t cdrSize;
    cdr >> cdrSize;
    size_t size = static_cast<size_t>(cdrSize);

    // Check there are at least 'size' remaining bytes in the CDR stream before resizing
    auto old_state = cdr.getState();
    bool correct_size = cdr.jump(size);
    cdr.setState(old_state);
    if (!correct_size) {
      fprintf(stderr, "sequence size exceeds remaining buffer\n");
      return false;
    }

    if (ros_message->probabilities.data) {
      rosidl_runtime_c__float__Sequence__fini(&ros_message->probabilities);
    }
    if (!rosidl_runtime_c__float__Sequence__init(&ros_message->probabilities, size)) {
      fprintf(stderr, "failed to create array for field 'probabilities'");
      return false;
    }
    auto array_ptr = ros_message->probabilities.data;
    cdr.deserializeArray(array_ptr, size);
  }

  return true;
}  // NOLINT(readability/fn_size)

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_robot_object_detector_ros
size_t get_serialized_size_robot_object_detector_ros__msg__FruitClassification(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _FruitClassification__ros_msg_type * ros_message = static_cast<const _FruitClassification__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // field.name cube

  current_alignment += get_serialized_size_robot_object_detector_ros__msg__Detection2D(
    &(ros_message->cube), current_alignment);
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
  // field.name pick_allowed
  {
    size_t item_size = sizeof(ros_message->pick_allowed);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name class_names
  {
    size_t array_size = ros_message->class_names.size;
    auto array_ptr = ros_message->class_names.data;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += padding +
        eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
        (array_ptr[index].size + 1);
    }
  }
  // field.name probabilities
  {
    size_t array_size = ros_message->probabilities.size;
    auto array_ptr = ros_message->probabilities.data;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    (void)array_ptr;
    size_t item_size = sizeof(array_ptr[0]);
    current_alignment += array_size * item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

static uint32_t _FruitClassification__get_serialized_size(const void * untyped_ros_message)
{
  return static_cast<uint32_t>(
    get_serialized_size_robot_object_detector_ros__msg__FruitClassification(
      untyped_ros_message, 0));
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_robot_object_detector_ros
size_t max_serialized_size_robot_object_detector_ros__msg__FruitClassification(
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

  // member: cube
  {
    size_t array_size = 1;


    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size;
      inner_size =
        max_serialized_size_robot_object_detector_ros__msg__Detection2D(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
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
  // member: pick_allowed
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: class_names
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
  // member: probabilities
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
    using DataType = robot_object_detector_ros__msg__FruitClassification;
    is_plain =
      (
      offsetof(DataType, probabilities) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}

static size_t _FruitClassification__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_robot_object_detector_ros__msg__FruitClassification(
    full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}


static message_type_support_callbacks_t __callbacks_FruitClassification = {
  "robot_object_detector_ros::msg",
  "FruitClassification",
  _FruitClassification__cdr_serialize,
  _FruitClassification__cdr_deserialize,
  _FruitClassification__get_serialized_size,
  _FruitClassification__max_serialized_size
};

static rosidl_message_type_support_t _FruitClassification__type_support = {
  rosidl_typesupport_fastrtps_c__identifier,
  &__callbacks_FruitClassification,
  get_message_typesupport_handle_function,
};

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, robot_object_detector_ros, msg, FruitClassification)() {
  return &_FruitClassification__type_support;
}

#if defined(__cplusplus)
}
#endif
