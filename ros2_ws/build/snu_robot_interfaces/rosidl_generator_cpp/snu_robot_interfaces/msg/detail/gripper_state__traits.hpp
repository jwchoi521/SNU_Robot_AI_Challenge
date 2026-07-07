// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from snu_robot_interfaces:msg/GripperState.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_STATE__TRAITS_HPP_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_STATE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "snu_robot_interfaces/msg/detail/gripper_state__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace snu_robot_interfaces
{

namespace msg
{

inline void to_flow_style_yaml(
  const GripperState & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: is_open
  {
    out << "is_open: ";
    rosidl_generator_traits::value_to_yaml(msg.is_open, out);
    out << ", ";
  }

  // member: is_closed
  {
    out << "is_closed: ";
    rosidl_generator_traits::value_to_yaml(msg.is_closed, out);
    out << ", ";
  }

  // member: has_object
  {
    out << "has_object: ";
    rosidl_generator_traits::value_to_yaml(msg.has_object, out);
    out << ", ";
  }

  // member: opening_m
  {
    out << "opening_m: ";
    rosidl_generator_traits::value_to_yaml(msg.opening_m, out);
    out << ", ";
  }

  // member: effort
  {
    out << "effort: ";
    rosidl_generator_traits::value_to_yaml(msg.effort, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const GripperState & msg,
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

  // member: is_open
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "is_open: ";
    rosidl_generator_traits::value_to_yaml(msg.is_open, out);
    out << "\n";
  }

  // member: is_closed
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "is_closed: ";
    rosidl_generator_traits::value_to_yaml(msg.is_closed, out);
    out << "\n";
  }

  // member: has_object
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "has_object: ";
    rosidl_generator_traits::value_to_yaml(msg.has_object, out);
    out << "\n";
  }

  // member: opening_m
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "opening_m: ";
    rosidl_generator_traits::value_to_yaml(msg.opening_m, out);
    out << "\n";
  }

  // member: effort
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "effort: ";
    rosidl_generator_traits::value_to_yaml(msg.effort, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const GripperState & msg, bool use_flow_style = false)
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
  const snu_robot_interfaces::msg::GripperState & msg,
  std::ostream & out, size_t indentation = 0)
{
  snu_robot_interfaces::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use snu_robot_interfaces::msg::to_yaml() instead")]]
inline std::string to_yaml(const snu_robot_interfaces::msg::GripperState & msg)
{
  return snu_robot_interfaces::msg::to_yaml(msg);
}

template<>
inline const char * data_type<snu_robot_interfaces::msg::GripperState>()
{
  return "snu_robot_interfaces::msg::GripperState";
}

template<>
inline const char * name<snu_robot_interfaces::msg::GripperState>()
{
  return "snu_robot_interfaces/msg/GripperState";
}

template<>
struct has_fixed_size<snu_robot_interfaces::msg::GripperState>
  : std::integral_constant<bool, has_fixed_size<std_msgs::msg::Header>::value> {};

template<>
struct has_bounded_size<snu_robot_interfaces::msg::GripperState>
  : std::integral_constant<bool, has_bounded_size<std_msgs::msg::Header>::value> {};

template<>
struct is_message<snu_robot_interfaces::msg::GripperState>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_STATE__TRAITS_HPP_
