// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from robot_object_detector_ros:msg/FruitClassification.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION__BUILDER_HPP_
#define ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "robot_object_detector_ros/msg/detail/fruit_classification__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace robot_object_detector_ros
{

namespace msg
{

namespace builder
{

class Init_FruitClassification_probabilities
{
public:
  explicit Init_FruitClassification_probabilities(::robot_object_detector_ros::msg::FruitClassification & msg)
  : msg_(msg)
  {}
  ::robot_object_detector_ros::msg::FruitClassification probabilities(::robot_object_detector_ros::msg::FruitClassification::_probabilities_type arg)
  {
    msg_.probabilities = std::move(arg);
    return std::move(msg_);
  }

private:
  ::robot_object_detector_ros::msg::FruitClassification msg_;
};

class Init_FruitClassification_class_names
{
public:
  explicit Init_FruitClassification_class_names(::robot_object_detector_ros::msg::FruitClassification & msg)
  : msg_(msg)
  {}
  Init_FruitClassification_probabilities class_names(::robot_object_detector_ros::msg::FruitClassification::_class_names_type arg)
  {
    msg_.class_names = std::move(arg);
    return Init_FruitClassification_probabilities(msg_);
  }

private:
  ::robot_object_detector_ros::msg::FruitClassification msg_;
};

class Init_FruitClassification_pick_allowed
{
public:
  explicit Init_FruitClassification_pick_allowed(::robot_object_detector_ros::msg::FruitClassification & msg)
  : msg_(msg)
  {}
  Init_FruitClassification_class_names pick_allowed(::robot_object_detector_ros::msg::FruitClassification::_pick_allowed_type arg)
  {
    msg_.pick_allowed = std::move(arg);
    return Init_FruitClassification_class_names(msg_);
  }

private:
  ::robot_object_detector_ros::msg::FruitClassification msg_;
};

class Init_FruitClassification_confidence
{
public:
  explicit Init_FruitClassification_confidence(::robot_object_detector_ros::msg::FruitClassification & msg)
  : msg_(msg)
  {}
  Init_FruitClassification_pick_allowed confidence(::robot_object_detector_ros::msg::FruitClassification::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return Init_FruitClassification_pick_allowed(msg_);
  }

private:
  ::robot_object_detector_ros::msg::FruitClassification msg_;
};

class Init_FruitClassification_fruit_kind
{
public:
  explicit Init_FruitClassification_fruit_kind(::robot_object_detector_ros::msg::FruitClassification & msg)
  : msg_(msg)
  {}
  Init_FruitClassification_confidence fruit_kind(::robot_object_detector_ros::msg::FruitClassification::_fruit_kind_type arg)
  {
    msg_.fruit_kind = std::move(arg);
    return Init_FruitClassification_confidence(msg_);
  }

private:
  ::robot_object_detector_ros::msg::FruitClassification msg_;
};

class Init_FruitClassification_cube
{
public:
  Init_FruitClassification_cube()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FruitClassification_fruit_kind cube(::robot_object_detector_ros::msg::FruitClassification::_cube_type arg)
  {
    msg_.cube = std::move(arg);
    return Init_FruitClassification_fruit_kind(msg_);
  }

private:
  ::robot_object_detector_ros::msg::FruitClassification msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_object_detector_ros::msg::FruitClassification>()
{
  return robot_object_detector_ros::msg::builder::Init_FruitClassification_cube();
}

}  // namespace robot_object_detector_ros

#endif  // ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION__BUILDER_HPP_
