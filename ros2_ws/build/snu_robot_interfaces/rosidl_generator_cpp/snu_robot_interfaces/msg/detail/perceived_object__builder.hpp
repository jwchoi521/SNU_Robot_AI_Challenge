// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from snu_robot_interfaces:msg/PerceivedObject.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__PERCEIVED_OBJECT__BUILDER_HPP_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__PERCEIVED_OBJECT__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "snu_robot_interfaces/msg/detail/perceived_object__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace snu_robot_interfaces
{

namespace msg
{

namespace builder
{

class Init_PerceivedObject_target_confirmed
{
public:
  explicit Init_PerceivedObject_target_confirmed(::snu_robot_interfaces::msg::PerceivedObject & msg)
  : msg_(msg)
  {}
  ::snu_robot_interfaces::msg::PerceivedObject target_confirmed(::snu_robot_interfaces::msg::PerceivedObject::_target_confirmed_type arg)
  {
    msg_.target_confirmed = std::move(arg);
    return std::move(msg_);
  }

private:
  ::snu_robot_interfaces::msg::PerceivedObject msg_;
};

class Init_PerceivedObject_pick_allowed
{
public:
  explicit Init_PerceivedObject_pick_allowed(::snu_robot_interfaces::msg::PerceivedObject & msg)
  : msg_(msg)
  {}
  Init_PerceivedObject_target_confirmed pick_allowed(::snu_robot_interfaces::msg::PerceivedObject::_pick_allowed_type arg)
  {
    msg_.pick_allowed = std::move(arg);
    return Init_PerceivedObject_target_confirmed(msg_);
  }

private:
  ::snu_robot_interfaces::msg::PerceivedObject msg_;
};

class Init_PerceivedObject_obstacle_radius_m
{
public:
  explicit Init_PerceivedObject_obstacle_radius_m(::snu_robot_interfaces::msg::PerceivedObject & msg)
  : msg_(msg)
  {}
  Init_PerceivedObject_pick_allowed obstacle_radius_m(::snu_robot_interfaces::msg::PerceivedObject::_obstacle_radius_m_type arg)
  {
    msg_.obstacle_radius_m = std::move(arg);
    return Init_PerceivedObject_pick_allowed(msg_);
  }

private:
  ::snu_robot_interfaces::msg::PerceivedObject msg_;
};

class Init_PerceivedObject_distance_m
{
public:
  explicit Init_PerceivedObject_distance_m(::snu_robot_interfaces::msg::PerceivedObject & msg)
  : msg_(msg)
  {}
  Init_PerceivedObject_obstacle_radius_m distance_m(::snu_robot_interfaces::msg::PerceivedObject::_distance_m_type arg)
  {
    msg_.distance_m = std::move(arg);
    return Init_PerceivedObject_obstacle_radius_m(msg_);
  }

private:
  ::snu_robot_interfaces::msg::PerceivedObject msg_;
};

class Init_PerceivedObject_has_distance
{
public:
  explicit Init_PerceivedObject_has_distance(::snu_robot_interfaces::msg::PerceivedObject & msg)
  : msg_(msg)
  {}
  Init_PerceivedObject_distance_m has_distance(::snu_robot_interfaces::msg::PerceivedObject::_has_distance_type arg)
  {
    msg_.has_distance = std::move(arg);
    return Init_PerceivedObject_distance_m(msg_);
  }

private:
  ::snu_robot_interfaces::msg::PerceivedObject msg_;
};

class Init_PerceivedObject_bearing_deg
{
public:
  explicit Init_PerceivedObject_bearing_deg(::snu_robot_interfaces::msg::PerceivedObject & msg)
  : msg_(msg)
  {}
  Init_PerceivedObject_has_distance bearing_deg(::snu_robot_interfaces::msg::PerceivedObject::_bearing_deg_type arg)
  {
    msg_.bearing_deg = std::move(arg);
    return Init_PerceivedObject_has_distance(msg_);
  }

private:
  ::snu_robot_interfaces::msg::PerceivedObject msg_;
};

class Init_PerceivedObject_bbox_y2
{
public:
  explicit Init_PerceivedObject_bbox_y2(::snu_robot_interfaces::msg::PerceivedObject & msg)
  : msg_(msg)
  {}
  Init_PerceivedObject_bearing_deg bbox_y2(::snu_robot_interfaces::msg::PerceivedObject::_bbox_y2_type arg)
  {
    msg_.bbox_y2 = std::move(arg);
    return Init_PerceivedObject_bearing_deg(msg_);
  }

private:
  ::snu_robot_interfaces::msg::PerceivedObject msg_;
};

class Init_PerceivedObject_bbox_x2
{
public:
  explicit Init_PerceivedObject_bbox_x2(::snu_robot_interfaces::msg::PerceivedObject & msg)
  : msg_(msg)
  {}
  Init_PerceivedObject_bbox_y2 bbox_x2(::snu_robot_interfaces::msg::PerceivedObject::_bbox_x2_type arg)
  {
    msg_.bbox_x2 = std::move(arg);
    return Init_PerceivedObject_bbox_y2(msg_);
  }

private:
  ::snu_robot_interfaces::msg::PerceivedObject msg_;
};

class Init_PerceivedObject_bbox_y1
{
public:
  explicit Init_PerceivedObject_bbox_y1(::snu_robot_interfaces::msg::PerceivedObject & msg)
  : msg_(msg)
  {}
  Init_PerceivedObject_bbox_x2 bbox_y1(::snu_robot_interfaces::msg::PerceivedObject::_bbox_y1_type arg)
  {
    msg_.bbox_y1 = std::move(arg);
    return Init_PerceivedObject_bbox_x2(msg_);
  }

private:
  ::snu_robot_interfaces::msg::PerceivedObject msg_;
};

class Init_PerceivedObject_bbox_x1
{
public:
  explicit Init_PerceivedObject_bbox_x1(::snu_robot_interfaces::msg::PerceivedObject & msg)
  : msg_(msg)
  {}
  Init_PerceivedObject_bbox_y1 bbox_x1(::snu_robot_interfaces::msg::PerceivedObject::_bbox_x1_type arg)
  {
    msg_.bbox_x1 = std::move(arg);
    return Init_PerceivedObject_bbox_y1(msg_);
  }

private:
  ::snu_robot_interfaces::msg::PerceivedObject msg_;
};

class Init_PerceivedObject_confidence
{
public:
  explicit Init_PerceivedObject_confidence(::snu_robot_interfaces::msg::PerceivedObject & msg)
  : msg_(msg)
  {}
  Init_PerceivedObject_bbox_x1 confidence(::snu_robot_interfaces::msg::PerceivedObject::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return Init_PerceivedObject_bbox_x1(msg_);
  }

private:
  ::snu_robot_interfaces::msg::PerceivedObject msg_;
};

class Init_PerceivedObject_navigation_role
{
public:
  explicit Init_PerceivedObject_navigation_role(::snu_robot_interfaces::msg::PerceivedObject & msg)
  : msg_(msg)
  {}
  Init_PerceivedObject_confidence navigation_role(::snu_robot_interfaces::msg::PerceivedObject::_navigation_role_type arg)
  {
    msg_.navigation_role = std::move(arg);
    return Init_PerceivedObject_confidence(msg_);
  }

private:
  ::snu_robot_interfaces::msg::PerceivedObject msg_;
};

class Init_PerceivedObject_fruit_kind
{
public:
  explicit Init_PerceivedObject_fruit_kind(::snu_robot_interfaces::msg::PerceivedObject & msg)
  : msg_(msg)
  {}
  Init_PerceivedObject_navigation_role fruit_kind(::snu_robot_interfaces::msg::PerceivedObject::_fruit_kind_type arg)
  {
    msg_.fruit_kind = std::move(arg);
    return Init_PerceivedObject_navigation_role(msg_);
  }

private:
  ::snu_robot_interfaces::msg::PerceivedObject msg_;
};

class Init_PerceivedObject_object_kind
{
public:
  Init_PerceivedObject_object_kind()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_PerceivedObject_fruit_kind object_kind(::snu_robot_interfaces::msg::PerceivedObject::_object_kind_type arg)
  {
    msg_.object_kind = std::move(arg);
    return Init_PerceivedObject_fruit_kind(msg_);
  }

private:
  ::snu_robot_interfaces::msg::PerceivedObject msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::snu_robot_interfaces::msg::PerceivedObject>()
{
  return snu_robot_interfaces::msg::builder::Init_PerceivedObject_object_kind();
}

}  // namespace snu_robot_interfaces

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__PERCEIVED_OBJECT__BUILDER_HPP_
