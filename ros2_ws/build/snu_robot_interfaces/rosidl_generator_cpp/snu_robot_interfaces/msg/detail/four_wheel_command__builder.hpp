// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from snu_robot_interfaces:msg/FourWheelCommand.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__FOUR_WHEEL_COMMAND__BUILDER_HPP_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__FOUR_WHEEL_COMMAND__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "snu_robot_interfaces/msg/detail/four_wheel_command__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace snu_robot_interfaces
{

namespace msg
{

namespace builder
{

class Init_FourWheelCommand_rear_right
{
public:
  explicit Init_FourWheelCommand_rear_right(::snu_robot_interfaces::msg::FourWheelCommand & msg)
  : msg_(msg)
  {}
  ::snu_robot_interfaces::msg::FourWheelCommand rear_right(::snu_robot_interfaces::msg::FourWheelCommand::_rear_right_type arg)
  {
    msg_.rear_right = std::move(arg);
    return std::move(msg_);
  }

private:
  ::snu_robot_interfaces::msg::FourWheelCommand msg_;
};

class Init_FourWheelCommand_rear_left
{
public:
  explicit Init_FourWheelCommand_rear_left(::snu_robot_interfaces::msg::FourWheelCommand & msg)
  : msg_(msg)
  {}
  Init_FourWheelCommand_rear_right rear_left(::snu_robot_interfaces::msg::FourWheelCommand::_rear_left_type arg)
  {
    msg_.rear_left = std::move(arg);
    return Init_FourWheelCommand_rear_right(msg_);
  }

private:
  ::snu_robot_interfaces::msg::FourWheelCommand msg_;
};

class Init_FourWheelCommand_front_right
{
public:
  explicit Init_FourWheelCommand_front_right(::snu_robot_interfaces::msg::FourWheelCommand & msg)
  : msg_(msg)
  {}
  Init_FourWheelCommand_rear_left front_right(::snu_robot_interfaces::msg::FourWheelCommand::_front_right_type arg)
  {
    msg_.front_right = std::move(arg);
    return Init_FourWheelCommand_rear_left(msg_);
  }

private:
  ::snu_robot_interfaces::msg::FourWheelCommand msg_;
};

class Init_FourWheelCommand_front_left
{
public:
  explicit Init_FourWheelCommand_front_left(::snu_robot_interfaces::msg::FourWheelCommand & msg)
  : msg_(msg)
  {}
  Init_FourWheelCommand_front_right front_left(::snu_robot_interfaces::msg::FourWheelCommand::_front_left_type arg)
  {
    msg_.front_left = std::move(arg);
    return Init_FourWheelCommand_front_right(msg_);
  }

private:
  ::snu_robot_interfaces::msg::FourWheelCommand msg_;
};

class Init_FourWheelCommand_command_mode
{
public:
  explicit Init_FourWheelCommand_command_mode(::snu_robot_interfaces::msg::FourWheelCommand & msg)
  : msg_(msg)
  {}
  Init_FourWheelCommand_front_left command_mode(::snu_robot_interfaces::msg::FourWheelCommand::_command_mode_type arg)
  {
    msg_.command_mode = std::move(arg);
    return Init_FourWheelCommand_front_left(msg_);
  }

private:
  ::snu_robot_interfaces::msg::FourWheelCommand msg_;
};

class Init_FourWheelCommand_header
{
public:
  Init_FourWheelCommand_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FourWheelCommand_command_mode header(::snu_robot_interfaces::msg::FourWheelCommand::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FourWheelCommand_command_mode(msg_);
  }

private:
  ::snu_robot_interfaces::msg::FourWheelCommand msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::snu_robot_interfaces::msg::FourWheelCommand>()
{
  return snu_robot_interfaces::msg::builder::Init_FourWheelCommand_header();
}

}  // namespace snu_robot_interfaces

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__FOUR_WHEEL_COMMAND__BUILDER_HPP_
