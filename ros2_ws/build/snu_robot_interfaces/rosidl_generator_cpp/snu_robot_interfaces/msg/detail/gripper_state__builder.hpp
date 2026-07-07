// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from snu_robot_interfaces:msg/GripperState.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_STATE__BUILDER_HPP_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_STATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "snu_robot_interfaces/msg/detail/gripper_state__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace snu_robot_interfaces
{

namespace msg
{

namespace builder
{

class Init_GripperState_effort
{
public:
  explicit Init_GripperState_effort(::snu_robot_interfaces::msg::GripperState & msg)
  : msg_(msg)
  {}
  ::snu_robot_interfaces::msg::GripperState effort(::snu_robot_interfaces::msg::GripperState::_effort_type arg)
  {
    msg_.effort = std::move(arg);
    return std::move(msg_);
  }

private:
  ::snu_robot_interfaces::msg::GripperState msg_;
};

class Init_GripperState_opening_m
{
public:
  explicit Init_GripperState_opening_m(::snu_robot_interfaces::msg::GripperState & msg)
  : msg_(msg)
  {}
  Init_GripperState_effort opening_m(::snu_robot_interfaces::msg::GripperState::_opening_m_type arg)
  {
    msg_.opening_m = std::move(arg);
    return Init_GripperState_effort(msg_);
  }

private:
  ::snu_robot_interfaces::msg::GripperState msg_;
};

class Init_GripperState_has_object
{
public:
  explicit Init_GripperState_has_object(::snu_robot_interfaces::msg::GripperState & msg)
  : msg_(msg)
  {}
  Init_GripperState_opening_m has_object(::snu_robot_interfaces::msg::GripperState::_has_object_type arg)
  {
    msg_.has_object = std::move(arg);
    return Init_GripperState_opening_m(msg_);
  }

private:
  ::snu_robot_interfaces::msg::GripperState msg_;
};

class Init_GripperState_is_closed
{
public:
  explicit Init_GripperState_is_closed(::snu_robot_interfaces::msg::GripperState & msg)
  : msg_(msg)
  {}
  Init_GripperState_has_object is_closed(::snu_robot_interfaces::msg::GripperState::_is_closed_type arg)
  {
    msg_.is_closed = std::move(arg);
    return Init_GripperState_has_object(msg_);
  }

private:
  ::snu_robot_interfaces::msg::GripperState msg_;
};

class Init_GripperState_is_open
{
public:
  explicit Init_GripperState_is_open(::snu_robot_interfaces::msg::GripperState & msg)
  : msg_(msg)
  {}
  Init_GripperState_is_closed is_open(::snu_robot_interfaces::msg::GripperState::_is_open_type arg)
  {
    msg_.is_open = std::move(arg);
    return Init_GripperState_is_closed(msg_);
  }

private:
  ::snu_robot_interfaces::msg::GripperState msg_;
};

class Init_GripperState_header
{
public:
  Init_GripperState_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_GripperState_is_open header(::snu_robot_interfaces::msg::GripperState::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_GripperState_is_open(msg_);
  }

private:
  ::snu_robot_interfaces::msg::GripperState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::snu_robot_interfaces::msg::GripperState>()
{
  return snu_robot_interfaces::msg::builder::Init_GripperState_header();
}

}  // namespace snu_robot_interfaces

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_STATE__BUILDER_HPP_
