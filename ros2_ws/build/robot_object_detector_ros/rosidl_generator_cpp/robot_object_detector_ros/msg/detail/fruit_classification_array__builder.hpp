// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from robot_object_detector_ros:msg/FruitClassificationArray.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION_ARRAY__BUILDER_HPP_
#define ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION_ARRAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "robot_object_detector_ros/msg/detail/fruit_classification_array__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace robot_object_detector_ros
{

namespace msg
{

namespace builder
{

class Init_FruitClassificationArray_classifications
{
public:
  explicit Init_FruitClassificationArray_classifications(::robot_object_detector_ros::msg::FruitClassificationArray & msg)
  : msg_(msg)
  {}
  ::robot_object_detector_ros::msg::FruitClassificationArray classifications(::robot_object_detector_ros::msg::FruitClassificationArray::_classifications_type arg)
  {
    msg_.classifications = std::move(arg);
    return std::move(msg_);
  }

private:
  ::robot_object_detector_ros::msg::FruitClassificationArray msg_;
};

class Init_FruitClassificationArray_header
{
public:
  Init_FruitClassificationArray_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FruitClassificationArray_classifications header(::robot_object_detector_ros::msg::FruitClassificationArray::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FruitClassificationArray_classifications(msg_);
  }

private:
  ::robot_object_detector_ros::msg::FruitClassificationArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_object_detector_ros::msg::FruitClassificationArray>()
{
  return robot_object_detector_ros::msg::builder::Init_FruitClassificationArray_header();
}

}  // namespace robot_object_detector_ros

#endif  // ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION_ARRAY__BUILDER_HPP_
