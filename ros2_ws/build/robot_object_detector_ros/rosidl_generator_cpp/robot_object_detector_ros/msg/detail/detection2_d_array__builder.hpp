// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from robot_object_detector_ros:msg/Detection2DArray.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__DETECTION2_D_ARRAY__BUILDER_HPP_
#define ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__DETECTION2_D_ARRAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "robot_object_detector_ros/msg/detail/detection2_d_array__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace robot_object_detector_ros
{

namespace msg
{

namespace builder
{

class Init_Detection2DArray_detections
{
public:
  explicit Init_Detection2DArray_detections(::robot_object_detector_ros::msg::Detection2DArray & msg)
  : msg_(msg)
  {}
  ::robot_object_detector_ros::msg::Detection2DArray detections(::robot_object_detector_ros::msg::Detection2DArray::_detections_type arg)
  {
    msg_.detections = std::move(arg);
    return std::move(msg_);
  }

private:
  ::robot_object_detector_ros::msg::Detection2DArray msg_;
};

class Init_Detection2DArray_header
{
public:
  Init_Detection2DArray_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Detection2DArray_detections header(::robot_object_detector_ros::msg::Detection2DArray::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_Detection2DArray_detections(msg_);
  }

private:
  ::robot_object_detector_ros::msg::Detection2DArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_object_detector_ros::msg::Detection2DArray>()
{
  return robot_object_detector_ros::msg::builder::Init_Detection2DArray_header();
}

}  // namespace robot_object_detector_ros

#endif  // ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__DETECTION2_D_ARRAY__BUILDER_HPP_
