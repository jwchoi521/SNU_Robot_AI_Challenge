// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from snu_robot_interfaces:msg/FourWheelCommand.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__FOUR_WHEEL_COMMAND__TRAITS_HPP_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__FOUR_WHEEL_COMMAND__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "snu_robot_interfaces/msg/detail/four_wheel_command__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace snu_robot_interfaces
{

namespace msg
{

inline void to_flow_style_yaml(
  const FourWheelCommand & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: command_mode
  {
    out << "command_mode: ";
    rosidl_generator_traits::value_to_yaml(msg.command_mode, out);
    out << ", ";
  }

  // member: front_left
  {
    out << "front_left: ";
    rosidl_generator_traits::value_to_yaml(msg.front_left, out);
    out << ", ";
  }

  // member: front_right
  {
    out << "front_right: ";
    rosidl_generator_traits::value_to_yaml(msg.front_right, out);
    out << ", ";
  }

  // member: rear_left
  {
    out << "rear_left: ";
    rosidl_generator_traits::value_to_yaml(msg.rear_left, out);
    out << ", ";
  }

  // member: rear_right
  {
    out << "rear_right: ";
    rosidl_generator_traits::value_to_yaml(msg.rear_right, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const FourWheelCommand & msg,
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

  // member: command_mode
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "command_mode: ";
    rosidl_generator_traits::value_to_yaml(msg.command_mode, out);
    out << "\n";
  }

  // member: front_left
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "front_left: ";
    rosidl_generator_traits::value_to_yaml(msg.front_left, out);
    out << "\n";
  }

  // member: front_right
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "front_right: ";
    rosidl_generator_traits::value_to_yaml(msg.front_right, out);
    out << "\n";
  }

  // member: rear_left
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "rear_left: ";
    rosidl_generator_traits::value_to_yaml(msg.rear_left, out);
    out << "\n";
  }

  // member: rear_right
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "rear_right: ";
    rosidl_generator_traits::value_to_yaml(msg.rear_right, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const FourWheelCommand & msg, bool use_flow_style = false)
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
  const snu_robot_interfaces::msg::FourWheelCommand & msg,
  std::ostream & out, size_t indentation = 0)
{
  snu_robot_interfaces::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use snu_robot_interfaces::msg::to_yaml() instead")]]
inline std::string to_yaml(const snu_robot_interfaces::msg::FourWheelCommand & msg)
{
  return snu_robot_interfaces::msg::to_yaml(msg);
}

template<>
inline const char * data_type<snu_robot_interfaces::msg::FourWheelCommand>()
{
  return "snu_robot_interfaces::msg::FourWheelCommand";
}

template<>
inline const char * name<snu_robot_interfaces::msg::FourWheelCommand>()
{
  return "snu_robot_interfaces/msg/FourWheelCommand";
}

template<>
struct has_fixed_size<snu_robot_interfaces::msg::FourWheelCommand>
  : std::integral_constant<bool, has_fixed_size<std_msgs::msg::Header>::value> {};

template<>
struct has_bounded_size<snu_robot_interfaces::msg::FourWheelCommand>
  : std::integral_constant<bool, has_bounded_size<std_msgs::msg::Header>::value> {};

template<>
struct is_message<snu_robot_interfaces::msg::FourWheelCommand>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__FOUR_WHEEL_COMMAND__TRAITS_HPP_
