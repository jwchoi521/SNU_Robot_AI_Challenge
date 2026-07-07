// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from robot_object_detector_ros:msg/FruitClassification.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION__STRUCT_HPP_
#define ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'cube'
#include "robot_object_detector_ros/msg/detail/detection2_d__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__robot_object_detector_ros__msg__FruitClassification __attribute__((deprecated))
#else
# define DEPRECATED__robot_object_detector_ros__msg__FruitClassification __declspec(deprecated)
#endif

namespace robot_object_detector_ros
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct FruitClassification_
{
  using Type = FruitClassification_<ContainerAllocator>;

  explicit FruitClassification_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : cube(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->fruit_kind = "";
      this->confidence = 0.0f;
      this->pick_allowed = false;
    }
  }

  explicit FruitClassification_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : cube(_alloc, _init),
    fruit_kind(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->fruit_kind = "";
      this->confidence = 0.0f;
      this->pick_allowed = false;
    }
  }

  // field types and members
  using _cube_type =
    robot_object_detector_ros::msg::Detection2D_<ContainerAllocator>;
  _cube_type cube;
  using _fruit_kind_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _fruit_kind_type fruit_kind;
  using _confidence_type =
    float;
  _confidence_type confidence;
  using _pick_allowed_type =
    bool;
  _pick_allowed_type pick_allowed;
  using _class_names_type =
    std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>>;
  _class_names_type class_names;
  using _probabilities_type =
    std::vector<float, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<float>>;
  _probabilities_type probabilities;

  // setters for named parameter idiom
  Type & set__cube(
    const robot_object_detector_ros::msg::Detection2D_<ContainerAllocator> & _arg)
  {
    this->cube = _arg;
    return *this;
  }
  Type & set__fruit_kind(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->fruit_kind = _arg;
    return *this;
  }
  Type & set__confidence(
    const float & _arg)
  {
    this->confidence = _arg;
    return *this;
  }
  Type & set__pick_allowed(
    const bool & _arg)
  {
    this->pick_allowed = _arg;
    return *this;
  }
  Type & set__class_names(
    const std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>> & _arg)
  {
    this->class_names = _arg;
    return *this;
  }
  Type & set__probabilities(
    const std::vector<float, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<float>> & _arg)
  {
    this->probabilities = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    robot_object_detector_ros::msg::FruitClassification_<ContainerAllocator> *;
  using ConstRawPtr =
    const robot_object_detector_ros::msg::FruitClassification_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<robot_object_detector_ros::msg::FruitClassification_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<robot_object_detector_ros::msg::FruitClassification_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      robot_object_detector_ros::msg::FruitClassification_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<robot_object_detector_ros::msg::FruitClassification_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      robot_object_detector_ros::msg::FruitClassification_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<robot_object_detector_ros::msg::FruitClassification_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<robot_object_detector_ros::msg::FruitClassification_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<robot_object_detector_ros::msg::FruitClassification_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__robot_object_detector_ros__msg__FruitClassification
    std::shared_ptr<robot_object_detector_ros::msg::FruitClassification_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__robot_object_detector_ros__msg__FruitClassification
    std::shared_ptr<robot_object_detector_ros::msg::FruitClassification_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const FruitClassification_ & other) const
  {
    if (this->cube != other.cube) {
      return false;
    }
    if (this->fruit_kind != other.fruit_kind) {
      return false;
    }
    if (this->confidence != other.confidence) {
      return false;
    }
    if (this->pick_allowed != other.pick_allowed) {
      return false;
    }
    if (this->class_names != other.class_names) {
      return false;
    }
    if (this->probabilities != other.probabilities) {
      return false;
    }
    return true;
  }
  bool operator!=(const FruitClassification_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct FruitClassification_

// alias to use template instance with default allocator
using FruitClassification =
  robot_object_detector_ros::msg::FruitClassification_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace robot_object_detector_ros

#endif  // ROBOT_OBJECT_DETECTOR_ROS__MSG__DETAIL__FRUIT_CLASSIFICATION__STRUCT_HPP_
