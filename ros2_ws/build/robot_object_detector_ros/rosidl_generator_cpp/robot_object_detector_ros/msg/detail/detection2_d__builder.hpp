// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from robot_object_detector_ros:msg/Detection2D.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__DETECTION2_D__BUILDER_HPP_
#define ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__DETECTION2_D__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "robot_object_detector_ros/msg/detail/detection2_d__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace robot_object_detector_ros
{

namespace msg
{

namespace builder
{

class Init_Detection2D_y2
{
public:
  explicit Init_Detection2D_y2(::robot_object_detector_ros::msg::Detection2D & msg)
  : msg_(msg)
  {}
  ::robot_object_detector_ros::msg::Detection2D y2(::robot_object_detector_ros::msg::Detection2D::_y2_type arg)
  {
    msg_.y2 = std::move(arg);
    return std::move(msg_);
  }

private:
  ::robot_object_detector_ros::msg::Detection2D msg_;
};

class Init_Detection2D_x2
{
public:
  explicit Init_Detection2D_x2(::robot_object_detector_ros::msg::Detection2D & msg)
  : msg_(msg)
  {}
  Init_Detection2D_y2 x2(::robot_object_detector_ros::msg::Detection2D::_x2_type arg)
  {
    msg_.x2 = std::move(arg);
    return Init_Detection2D_y2(msg_);
  }

private:
  ::robot_object_detector_ros::msg::Detection2D msg_;
};

class Init_Detection2D_y1
{
public:
  explicit Init_Detection2D_y1(::robot_object_detector_ros::msg::Detection2D & msg)
  : msg_(msg)
  {}
  Init_Detection2D_x2 y1(::robot_object_detector_ros::msg::Detection2D::_y1_type arg)
  {
    msg_.y1 = std::move(arg);
    return Init_Detection2D_x2(msg_);
  }

private:
  ::robot_object_detector_ros::msg::Detection2D msg_;
};

class Init_Detection2D_x1
{
public:
  explicit Init_Detection2D_x1(::robot_object_detector_ros::msg::Detection2D & msg)
  : msg_(msg)
  {}
  Init_Detection2D_y1 x1(::robot_object_detector_ros::msg::Detection2D::_x1_type arg)
  {
    msg_.x1 = std::move(arg);
    return Init_Detection2D_y1(msg_);
  }

private:
  ::robot_object_detector_ros::msg::Detection2D msg_;
};

class Init_Detection2D_confidence
{
public:
  explicit Init_Detection2D_confidence(::robot_object_detector_ros::msg::Detection2D & msg)
  : msg_(msg)
  {}
  Init_Detection2D_x1 confidence(::robot_object_detector_ros::msg::Detection2D::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return Init_Detection2D_x1(msg_);
  }

private:
  ::robot_object_detector_ros::msg::Detection2D msg_;
};

class Init_Detection2D_class_name
{
public:
  explicit Init_Detection2D_class_name(::robot_object_detector_ros::msg::Detection2D & msg)
  : msg_(msg)
  {}
  Init_Detection2D_confidence class_name(::robot_object_detector_ros::msg::Detection2D::_class_name_type arg)
  {
    msg_.class_name = std::move(arg);
    return Init_Detection2D_confidence(msg_);
  }

private:
  ::robot_object_detector_ros::msg::Detection2D msg_;
};

class Init_Detection2D_class_id
{
public:
  Init_Detection2D_class_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Detection2D_class_name class_id(::robot_object_detector_ros::msg::Detection2D::_class_id_type arg)
  {
    msg_.class_id = std::move(arg);
    return Init_Detection2D_class_name(msg_);
  }

private:
  ::robot_object_detector_ros::msg::Detection2D msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_object_detector_ros::msg::Detection2D>()
{
  return robot_object_detector_ros::msg::builder::Init_Detection2D_class_id();
}

}  // namespace robot_object_detector_ros

#endif  // ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__DETECTION2_D__BUILDER_HPP_
