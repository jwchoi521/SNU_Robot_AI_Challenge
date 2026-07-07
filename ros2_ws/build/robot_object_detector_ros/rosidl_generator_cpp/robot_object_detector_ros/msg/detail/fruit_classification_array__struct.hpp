// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from robot_object_detector_ros:msg/FruitClassificationArray.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION_ARRAY__STRUCT_HPP_
#define ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION_ARRAY__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.hpp"
// Member 'classifications'
#include "robot_object_detector_ros/msg/detail/fruit_classification__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__robot_object_detector_ros__msg__FruitClassificationArray __attribute__((deprecated))
#else
# define DEPRECATED__robot_object_detector_ros__msg__FruitClassificationArray __declspec(deprecated)
#endif

namespace robot_object_detector_ros
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct FruitClassificationArray_
{
  using Type = FruitClassificationArray_<ContainerAllocator>;

  explicit FruitClassificationArray_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    (void)_init;
  }

  explicit FruitClassificationArray_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _classifications_type =
    std::vector<robot_object_detector_ros::msg::FruitClassification_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<robot_object_detector_ros::msg::FruitClassification_<ContainerAllocator>>>;
  _classifications_type classifications;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__classifications(
    const std::vector<robot_object_detector_ros::msg::FruitClassification_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<robot_object_detector_ros::msg::FruitClassification_<ContainerAllocator>>> & _arg)
  {
    this->classifications = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    robot_object_detector_ros::msg::FruitClassificationArray_<ContainerAllocator> *;
  using ConstRawPtr =
    const robot_object_detector_ros::msg::FruitClassificationArray_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<robot_object_detector_ros::msg::FruitClassificationArray_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<robot_object_detector_ros::msg::FruitClassificationArray_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      robot_object_detector_ros::msg::FruitClassificationArray_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<robot_object_detector_ros::msg::FruitClassificationArray_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      robot_object_detector_ros::msg::FruitClassificationArray_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<robot_object_detector_ros::msg::FruitClassificationArray_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<robot_object_detector_ros::msg::FruitClassificationArray_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<robot_object_detector_ros::msg::FruitClassificationArray_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__robot_object_detector_ros__msg__FruitClassificationArray
    std::shared_ptr<robot_object_detector_ros::msg::FruitClassificationArray_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__robot_object_detector_ros__msg__FruitClassificationArray
    std::shared_ptr<robot_object_detector_ros::msg::FruitClassificationArray_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const FruitClassificationArray_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->classifications != other.classifications) {
      return false;
    }
    return true;
  }
  bool operator!=(const FruitClassificationArray_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct FruitClassificationArray_

// alias to use template instance with default allocator
using FruitClassificationArray =
  robot_object_detector_ros::msg::FruitClassificationArray_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace robot_object_detector_ros

#endif  // ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION_ARRAY__STRUCT_HPP_
