// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from snu_robot_interfaces:msg/DetectedTargetArray.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET_ARRAY__BUILDER_HPP_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET_ARRAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "snu_robot_interfaces/msg/detail/detected_target_array__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace snu_robot_interfaces
{

namespace msg
{

namespace builder
{

class Init_DetectedTargetArray_targets
{
public:
  explicit Init_DetectedTargetArray_targets(::snu_robot_interfaces::msg::DetectedTargetArray & msg)
  : msg_(msg)
  {}
  ::snu_robot_interfaces::msg::DetectedTargetArray targets(::snu_robot_interfaces::msg::DetectedTargetArray::_targets_type arg)
  {
    msg_.targets = std::move(arg);
    return std::move(msg_);
  }

private:
  ::snu_robot_interfaces::msg::DetectedTargetArray msg_;
};

class Init_DetectedTargetArray_header
{
public:
  Init_DetectedTargetArray_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DetectedTargetArray_targets header(::snu_robot_interfaces::msg::DetectedTargetArray::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_DetectedTargetArray_targets(msg_);
  }

private:
  ::snu_robot_interfaces::msg::DetectedTargetArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::snu_robot_interfaces::msg::DetectedTargetArray>()
{
  return snu_robot_interfaces::msg::builder::Init_DetectedTargetArray_header();
}

}  // namespace snu_robot_interfaces

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET_ARRAY__BUILDER_HPP_
