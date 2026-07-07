// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__rosidl_typesupport_fastrtps_cpp.hpp.em
// with input from robot_object_detector_ros:msg/FruitClassificationArray.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION_ARRAY__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_
#define ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION_ARRAY__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_

#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_interface/macros.h"
#include "robot_object_detector_ros/msg/rosidl_typesupport_fastrtps_cpp__visibility_control.h"
#include "robot_object_detector_ros/msg/detail/fruit_classification_array__struct.hpp"

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

#include "fastcdr/Cdr.h"

namespace robot_object_detector_ros
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_robot_object_detector_ros
cdr_serialize(
  const robot_object_detector_ros::msg::FruitClassificationArray & ros_message,
  eprosima::fastcdr::Cdr & cdr);

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_robot_object_detector_ros
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  robot_object_detector_ros::msg::FruitClassificationArray & ros_message);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_robot_object_detector_ros
get_serialized_size(
  const robot_object_detector_ros::msg::FruitClassificationArray & ros_message,
  size_t current_alignment);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_robot_object_detector_ros
max_serialized_size_FruitClassificationArray(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace robot_object_detector_ros

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_robot_object_detector_ros
const rosidl_message_type_support_t *
  ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, robot_object_detector_ros, msg, FruitClassificationArray)();

#ifdef __cplusplus
}
#endif

#endif  // ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION_ARRAY__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_
