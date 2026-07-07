// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from snu_robot_interfaces:msg/PerceivedObjectArray.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__PERCEIVED_OBJECT_ARRAY__BUILDER_HPP_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__PERCEIVED_OBJECT_ARRAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "snu_robot_interfaces/msg/detail/perceived_object_array__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace snu_robot_interfaces
{

namespace msg
{

namespace builder
{

class Init_PerceivedObjectArray_objects
{
public:
  explicit Init_PerceivedObjectArray_objects(::snu_robot_interfaces::msg::PerceivedObjectArray & msg)
  : msg_(msg)
  {}
  ::snu_robot_interfaces::msg::PerceivedObjectArray objects(::snu_robot_interfaces::msg::PerceivedObjectArray::_objects_type arg)
  {
    msg_.objects = std::move(arg);
    return std::move(msg_);
  }

private:
  ::snu_robot_interfaces::msg::PerceivedObjectArray msg_;
};

class Init_PerceivedObjectArray_header
{
public:
  Init_PerceivedObjectArray_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_PerceivedObjectArray_objects header(::snu_robot_interfaces::msg::PerceivedObjectArray::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_PerceivedObjectArray_objects(msg_);
  }

private:
  ::snu_robot_interfaces::msg::PerceivedObjectArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::snu_robot_interfaces::msg::PerceivedObjectArray>()
{
  return snu_robot_interfaces::msg::builder::Init_PerceivedObjectArray_header();
}

}  // namespace snu_robot_interfaces

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__PERCEIVED_OBJECT_ARRAY__BUILDER_HPP_
