// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from snu_robot_interfaces:msg/DetectedTargetArray.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET_ARRAY__TRAITS_HPP_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET_ARRAY__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "snu_robot_interfaces/msg/detail/detected_target_array__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"
// Member 'targets'
#include "snu_robot_interfaces/msg/detail/detected_target__traits.hpp"

namespace snu_robot_interfaces
{

namespace msg
{

inline void to_flow_style_yaml(
  const DetectedTargetArray & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: targets
  {
    if (msg.targets.size() == 0) {
      out << "targets: []";
    } else {
      out << "targets: [";
      size_t pending_items = msg.targets.size();
      for (auto item : msg.targets) {
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
  const DetectedTargetArray & msg,
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

  // member: targets
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.targets.size() == 0) {
      out << "targets: []\n";
    } else {
      out << "targets:\n";
      for (auto item : msg.targets) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const DetectedTargetArray & msg, bool use_flow_style = false)
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
  const snu_robot_interfaces::msg::DetectedTargetArray & msg,
  std::ostream & out, size_t indentation = 0)
{
  snu_robot_interfaces::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use snu_robot_interfaces::msg::to_yaml() instead")]]
inline std::string to_yaml(const snu_robot_interfaces::msg::DetectedTargetArray & msg)
{
  return snu_robot_interfaces::msg::to_yaml(msg);
}

template<>
inline const char * data_type<snu_robot_interfaces::msg::DetectedTargetArray>()
{
  return "snu_robot_interfaces::msg::DetectedTargetArray";
}

template<>
inline const char * name<snu_robot_interfaces::msg::DetectedTargetArray>()
{
  return "snu_robot_interfaces/msg/DetectedTargetArray";
}

template<>
struct has_fixed_size<snu_robot_interfaces::msg::DetectedTargetArray>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<snu_robot_interfaces::msg::DetectedTargetArray>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<snu_robot_interfaces::msg::DetectedTargetArray>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET_ARRAY__TRAITS_HPP_
