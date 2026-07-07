// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from snu_robot_interfaces:msg/GripperState.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_STATE__STRUCT_HPP_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_STATE__STRUCT_HPP_

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

#ifndef _WIN32
# define DEPRECATED__snu_robot_interfaces__msg__GripperState __attribute__((deprecated))
#else
# define DEPRECATED__snu_robot_interfaces__msg__GripperState __declspec(deprecated)
#endif

namespace snu_robot_interfaces
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct GripperState_
{
  using Type = GripperState_<ContainerAllocator>;

  explicit GripperState_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->is_open = false;
      this->is_closed = false;
      this->has_object = false;
      this->opening_m = 0.0f;
      this->effort = 0.0f;
    }
  }

  explicit GripperState_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->is_open = false;
      this->is_closed = false;
      this->has_object = false;
      this->opening_m = 0.0f;
      this->effort = 0.0f;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _is_open_type =
    bool;
  _is_open_type is_open;
  using _is_closed_type =
    bool;
  _is_closed_type is_closed;
  using _has_object_type =
    bool;
  _has_object_type has_object;
  using _opening_m_type =
    float;
  _opening_m_type opening_m;
  using _effort_type =
    float;
  _effort_type effort;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__is_open(
    const bool & _arg)
  {
    this->is_open = _arg;
    return *this;
  }
  Type & set__is_closed(
    const bool & _arg)
  {
    this->is_closed = _arg;
    return *this;
  }
  Type & set__has_object(
    const bool & _arg)
  {
    this->has_object = _arg;
    return *this;
  }
  Type & set__opening_m(
    const float & _arg)
  {
    this->opening_m = _arg;
    return *this;
  }
  Type & set__effort(
    const float & _arg)
  {
    this->effort = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    snu_robot_interfaces::msg::GripperState_<ContainerAllocator> *;
  using ConstRawPtr =
    const snu_robot_interfaces::msg::GripperState_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<snu_robot_interfaces::msg::GripperState_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<snu_robot_interfaces::msg::GripperState_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      snu_robot_interfaces::msg::GripperState_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<snu_robot_interfaces::msg::GripperState_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      snu_robot_interfaces::msg::GripperState_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<snu_robot_interfaces::msg::GripperState_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<snu_robot_interfaces::msg::GripperState_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<snu_robot_interfaces::msg::GripperState_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__snu_robot_interfaces__msg__GripperState
    std::shared_ptr<snu_robot_interfaces::msg::GripperState_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__snu_robot_interfaces__msg__GripperState
    std::shared_ptr<snu_robot_interfaces::msg::GripperState_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GripperState_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->is_open != other.is_open) {
      return false;
    }
    if (this->is_closed != other.is_closed) {
      return false;
    }
    if (this->has_object != other.has_object) {
      return false;
    }
    if (this->opening_m != other.opening_m) {
      return false;
    }
    if (this->effort != other.effort) {
      return false;
    }
    return true;
  }
  bool operator!=(const GripperState_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GripperState_

// alias to use template instance with default allocator
using GripperState =
  snu_robot_interfaces::msg::GripperState_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace snu_robot_interfaces

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_STATE__STRUCT_HPP_
