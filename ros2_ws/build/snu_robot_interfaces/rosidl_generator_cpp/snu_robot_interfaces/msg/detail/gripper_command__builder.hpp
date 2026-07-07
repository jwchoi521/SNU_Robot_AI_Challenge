// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from snu_robot_interfaces:msg/GripperCommand.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_COMMAND__BUILDER_HPP_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_COMMAND__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "snu_robot_interfaces/msg/detail/gripper_command__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace snu_robot_interfaces
{

namespace msg
{

namespace builder
{

class Init_GripperCommand_effort
{
public:
  explicit Init_GripperCommand_effort(::snu_robot_interfaces::msg::GripperCommand & msg)
  : msg_(msg)
  {}
  ::snu_robot_interfaces::msg::GripperCommand effort(::snu_robot_interfaces::msg::GripperCommand::_effort_type arg)
  {
    msg_.effort = std::move(arg);
    return std::move(msg_);
  }

private:
  ::snu_robot_interfaces::msg::GripperCommand msg_;
};

class Init_GripperCommand_opening_m
{
public:
  explicit Init_GripperCommand_opening_m(::snu_robot_interfaces::msg::GripperCommand & msg)
  : msg_(msg)
  {}
  Init_GripperCommand_effort opening_m(::snu_robot_interfaces::msg::GripperCommand::_opening_m_type arg)
  {
    msg_.opening_m = std::move(arg);
    return Init_GripperCommand_effort(msg_);
  }

private:
  ::snu_robot_interfaces::msg::GripperCommand msg_;
};

class Init_GripperCommand_command
{
public:
  explicit Init_GripperCommand_command(::snu_robot_interfaces::msg::GripperCommand & msg)
  : msg_(msg)
  {}
  Init_GripperCommand_opening_m command(::snu_robot_interfaces::msg::GripperCommand::_command_type arg)
  {
    msg_.command = std::move(arg);
    return Init_GripperCommand_opening_m(msg_);
  }

private:
  ::snu_robot_interfaces::msg::GripperCommand msg_;
};

class Init_GripperCommand_header
{
public:
  Init_GripperCommand_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_GripperCommand_command header(::snu_robot_interfaces::msg::GripperCommand::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_GripperCommand_command(msg_);
  }

private:
  ::snu_robot_interfaces::msg::GripperCommand msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::snu_robot_interfaces::msg::GripperCommand>()
{
  return snu_robot_interfaces::msg::builder::Init_GripperCommand_header();
}

}  // namespace snu_robot_interfaces

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_COMMAND__BUILDER_HPP_
