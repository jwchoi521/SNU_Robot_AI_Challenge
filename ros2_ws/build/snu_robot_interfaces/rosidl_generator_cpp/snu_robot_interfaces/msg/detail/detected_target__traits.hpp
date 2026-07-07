// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from snu_robot_interfaces:msg/DetectedTarget.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET__TRAITS_HPP_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "snu_robot_interfaces/msg/detail/detected_target__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace snu_robot_interfaces
{

namespace msg
{

inline void to_flow_style_yaml(
  const DetectedTarget & msg,
  std::ostream & out)
{
  out << "{";
  // member: object_kind
  {
    out << "object_kind: ";
    rosidl_generator_traits::value_to_yaml(msg.object_kind, out);
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

  // member: bbox_x1
  {
    out << "bbox_x1: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_x1, out);
    out << ", ";
  }

  // member: bbox_y1
  {
    out << "bbox_y1: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_y1, out);
    out << ", ";
  }

  // member: bbox_x2
  {
    out << "bbox_x2: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_x2, out);
    out << ", ";
  }

  // member: bbox_y2
  {
    out << "bbox_y2: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_y2, out);
    out << ", ";
  }

  // member: bearing_deg
  {
    out << "bearing_deg: ";
    rosidl_generator_traits::value_to_yaml(msg.bearing_deg, out);
    out << ", ";
  }

  // member: has_distance
  {
    out << "has_distance: ";
    rosidl_generator_traits::value_to_yaml(msg.has_distance, out);
    out << ", ";
  }

  // member: distance_m
  {
    out << "distance_m: ";
    rosidl_generator_traits::value_to_yaml(msg.distance_m, out);
    out << ", ";
  }

  // member: pick_allowed
  {
    out << "pick_allowed: ";
    rosidl_generator_traits::value_to_yaml(msg.pick_allowed, out);
    out << ", ";
  }

  // member: target_confirmed
  {
    out << "target_confirmed: ";
    rosidl_generator_traits::value_to_yaml(msg.target_confirmed, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const DetectedTarget & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: object_kind
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "object_kind: ";
    rosidl_generator_traits::value_to_yaml(msg.object_kind, out);
    out << "\n";
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

  // member: bbox_x1
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "bbox_x1: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_x1, out);
    out << "\n";
  }

  // member: bbox_y1
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "bbox_y1: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_y1, out);
    out << "\n";
  }

  // member: bbox_x2
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "bbox_x2: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_x2, out);
    out << "\n";
  }

  // member: bbox_y2
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "bbox_y2: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_y2, out);
    out << "\n";
  }

  // member: bearing_deg
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "bearing_deg: ";
    rosidl_generator_traits::value_to_yaml(msg.bearing_deg, out);
    out << "\n";
  }

  // member: has_distance
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "has_distance: ";
    rosidl_generator_traits::value_to_yaml(msg.has_distance, out);
    out << "\n";
  }

  // member: distance_m
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "distance_m: ";
    rosidl_generator_traits::value_to_yaml(msg.distance_m, out);
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

  // member: target_confirmed
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "target_confirmed: ";
    rosidl_generator_traits::value_to_yaml(msg.target_confirmed, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const DetectedTarget & msg, bool use_flow_style = false)
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

}  // namespace snu_robot_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use snu_robot_interfaces::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const snu_robot_interfaces::msg::DetectedTarget & msg,
  std::ostream & out, size_t indentation = 0)
{
  snu_robot_interfaces::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use snu_robot_interfaces::msg::to_yaml() instead")]]
inline std::string to_yaml(const snu_robot_interfaces::msg::DetectedTarget & msg)
{
  return snu_robot_interfaces::msg::to_yaml(msg);
}

template<>
inline const char * data_type<snu_robot_interfaces::msg::DetectedTarget>()
{
  return "snu_robot_interfaces::msg::DetectedTarget";
}

template<>
inline const char * name<snu_robot_interfaces::msg::DetectedTarget>()
{
  return "snu_robot_interfaces/msg/DetectedTarget";
}

template<>
struct has_fixed_size<snu_robot_interfaces::msg::DetectedTarget>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<snu_robot_interfaces::msg::DetectedTarget>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<snu_robot_interfaces::msg::DetectedTarget>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET__TRAITS_HPP_
