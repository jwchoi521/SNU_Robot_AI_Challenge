// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from snu_robot_interfaces:msg/DetectedTargetArray.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET_ARRAY__STRUCT_HPP_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET_ARRAY__STRUCT_HPP_

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
// Member 'targets'
#include "snu_robot_interfaces/msg/detail/detected_target__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__snu_robot_interfaces__msg__DetectedTargetArray __attribute__((deprecated))
#else
# define DEPRECATED__snu_robot_interfaces__msg__DetectedTargetArray __declspec(deprecated)
#endif

namespace snu_robot_interfaces
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct DetectedTargetArray_
{
  using Type = DetectedTargetArray_<ContainerAllocator>;

  explicit DetectedTargetArray_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    (void)_init;
  }

  explicit DetectedTargetArray_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _targets_type =
    std::vector<snu_robot_interfaces::msg::DetectedTarget_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<snu_robot_interfaces::msg::DetectedTarget_<ContainerAllocator>>>;
  _targets_type targets;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__targets(
    const std::vector<snu_robot_interfaces::msg::DetectedTarget_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<snu_robot_interfaces::msg::DetectedTarget_<ContainerAllocator>>> & _arg)
  {
    this->targets = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    snu_robot_interfaces::msg::DetectedTargetArray_<ContainerAllocator> *;
  using ConstRawPtr =
    const snu_robot_interfaces::msg::DetectedTargetArray_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<snu_robot_interfaces::msg::DetectedTargetArray_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<snu_robot_interfaces::msg::DetectedTargetArray_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      snu_robot_interfaces::msg::DetectedTargetArray_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<snu_robot_interfaces::msg::DetectedTargetArray_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      snu_robot_interfaces::msg::DetectedTargetArray_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<snu_robot_interfaces::msg::DetectedTargetArray_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<snu_robot_interfaces::msg::DetectedTargetArray_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<snu_robot_interfaces::msg::DetectedTargetArray_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__snu_robot_interfaces__msg__DetectedTargetArray
    std::shared_ptr<snu_robot_interfaces::msg::DetectedTargetArray_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__snu_robot_interfaces__msg__DetectedTargetArray
    std::shared_ptr<snu_robot_interfaces::msg::DetectedTargetArray_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const DetectedTargetArray_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->targets != other.targets) {
      return false;
    }
    return true;
  }
  bool operator!=(const DetectedTargetArray_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct DetectedTargetArray_

// alias to use template instance with default allocator
using DetectedTargetArray =
  snu_robot_interfaces::msg::DetectedTargetArray_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace snu_robot_interfaces

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET_ARRAY__STRUCT_HPP_
