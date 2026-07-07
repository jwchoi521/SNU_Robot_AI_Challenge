// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from robot_object_detector_ros:msg/FruitClassification.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION__TRAITS_HPP_
#define ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "robot_object_detector_ros/msg/detail/fruit_classification__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'cube'
#include "robot_object_detector_ros/msg/detail/detection2_d__traits.hpp"

namespace robot_object_detector_ros
{

namespace msg
{

inline void to_flow_style_yaml(
  const FruitClassification & msg,
  std::ostream & out)
{
  out << "{";
  // member: cube
  {
    out << "cube: ";
    to_flow_style_yaml(msg.cube, out);
    out << ", ";
  }

  // member: fruit_kind
  {
    out << "fruit_kind: ";
    rosidl_generator_traits::value_to_yaml(msg.fruit_kind, out);
    out << ", ";
  }

  // member: confidence
  {
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << ", ";
  }

  // member: pick_allowed
  {
    out << "pick_allowed: ";
    rosidl_generator_traits::value_to_yaml(msg.pick_allowed, out);
    out << ", ";
  }

  // member: class_names
  {
    if (msg.class_names.size() == 0) {
      out << "class_names: []";
    } else {
      out << "class_names: [";
      size_t pending_items = msg.class_names.size();
      for (auto item : msg.class_names) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: probabilities
  {
    if (msg.probabilities.size() == 0) {
      out << "probabilities: []";
    } else {
      out << "probabilities: [";
      size_t pending_items = msg.probabilities.size();
      for (auto item : msg.probabilities) {
        rosidl_generator_traits::value_to_yaml(item, out);
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
  const FruitClassification & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: cube
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "cube:\n";
    to_block_style_yaml(msg.cube, out, indentation + 2);
  }

  // member: fruit_kind
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "fruit_kind: ";
    rosidl_generator_traits::value_to_yaml(msg.fruit_kind, out);
    out << "\n";
  }

  // member: confidence
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << "\n";
  }

  // member: pick_allowed
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "pick_allowed: ";
    rosidl_generator_traits::value_to_yaml(msg.pick_allowed, out);
    out << "\n";
  }

  // member: class_names
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.class_names.size() == 0) {
      out << "class_names: []\n";
    } else {
      out << "class_names:\n";
      for (auto item : msg.class_names) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: probabilities
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.probabilities.size() == 0) {
      out << "probabilities: []\n";
    } else {
      out << "probabilities:\n";
      for (auto item : msg.probabilities) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const FruitClassification & msg, bool use_flow_style = false)
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
  const robot_object_detector_ros::msg::FruitClassification & msg,
  std::ostream & out, size_t indentation = 0)
{
  robot_object_detector_ros::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use robot_object_detector_ros::msg::to_yaml() instead")]]
inline std::string to_yaml(const robot_object_detector_ros::msg::FruitClassification & msg)
{
  return robot_object_detector_ros::msg::to_yaml(msg);
}

template<>
inline const char * data_type<robot_object_detector_ros::msg::FruitClassification>()
{
  return "robot_object_detector_ros::msg::FruitClassification";
}

template<>
inline const char * name<robot_object_detector_ros::msg::FruitClassification>()
{
  return "robot_object_detector_ros/msg/FruitClassification";
}

template<>
struct has_fixed_size<robot_object_detector_ros::msg::FruitClassification>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<robot_object_detector_ros::msg::FruitClassification>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<robot_object_detector_ros::msg::FruitClassification>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION__TRAITS_HPP_
