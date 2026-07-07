// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from robot_object_detector_ros:msg/FruitClassificationArray.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION_ARRAY__TRAITS_HPP_
#define ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION_ARRAY__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "robot_object_detector_ros/msg/detail/fruit_classification_array__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"
// Member 'classifications'
#include "robot_object_detector_ros/msg/detail/fruit_classification__traits.hpp"

namespace robot_object_detector_ros
{

namespace msg
{

inline void to_flow_style_yaml(
  const FruitClassificationArray & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: classifications
  {
    if (msg.classifications.size() == 0) {
      out << "classifications: []";
    } else {
      out << "classifications: [";
      size_t pending_items = msg.classifications.size();
      for (auto item : msg.classifications) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const FruitClassificationArray & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: header
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "header:\n";
    to_block_style_yaml(msg.header, out, indentation + 2);
  }

  // member: classifications
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.classifications.size() == 0) {
      out << "classifications: []\n";
    } else {
      out << "classifications:\n";
      for (auto item : msg.classifications) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const FruitClassificationArray & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace robot_object_detector_ros

namespace rosidl_generator_traits
{

[[deprecated("use robot_object_detector_ros::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const robot_object_detector_ros::msg::FruitClassificationArray & msg,
  std::ostream & out, size_t indentation = 0)
{
  robot_object_detector_ros::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use robot_object_detector_ros::msg::to_yaml() instead")]]
inline std::string to_yaml(const robot_object_detector_ros::msg::FruitClassificationArray & msg)
{
  return robot_object_detector_ros::msg::to_yaml(msg);
}

template<>
inline const char * data_type<robot_object_detector_ros::msg::FruitClassificationArray>()
{
  return "robot_object_detector_ros::msg::FruitClassificationArray";
}

template<>
inline const char * name<robot_object_detector_ros::msg::FruitClassificationArray>()
{
  return "robot_object_detector_ros/msg/FruitClassificationArray";
}

template<>
struct has_fixed_size<robot_object_detector_ros::msg::FruitClassificationArray>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<robot_object_detector_ros::msg::FruitClassificationArray>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<robot_object_detector_ros::msg::FruitClassificationArray>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION_ARRAY__TRAITS_HPP_
