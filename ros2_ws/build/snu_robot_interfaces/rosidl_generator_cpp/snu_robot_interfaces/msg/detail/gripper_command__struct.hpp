// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from snu_robot_interfaces:msg/GripperCommand.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_COMMAND__STRUCT_HPP_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_COMMAND__STRUCT_HPP_

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
# define DEPRECATED__snu_robot_interfaces__msg__GripperCommand __attribute__((deprecated))
#else
# define DEPRECATED__snu_robot_interfaces__msg__GripperCommand __declspec(deprecated)
#endif

namespace snu_robot_interfaces
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct GripperCommand_
{
  using Type = GripperCommand_<ContainerAllocator>;

  explicit GripperCommand_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->command = 0;
      this->opening_m = 0.0f;
      this->effort = 0.0f;
    }
  }

  explicit GripperCommand_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->command = 0;
      this->opening_m = 0.0f;
      this->effort = 0.0f;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _command_type =
    uint8_t;
  _command_type command;
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
  Type & set__command(
    const uint8_t & _arg)
  {
    this->command = _arg;
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
  static constexpr uint8_t OPEN =
    1u;
  static constexpr uint8_t CLOSE =
    2u;
  static constexpr uint8_t STOP =
    3u;
  static constexpr uint8_t SET_OPENING =
    4u;

  // pointer types
  using RawPtr =
    snu_robot_interfaces::msg::GripperCommand_<ContainerAllocator> *;
  using ConstRawPtr =
    const snu_robot_interfaces::msg::GripperCommand_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<snu_robot_interfaces::msg::GripperCommand_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<snu_robot_interfaces::msg::GripperCommand_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      snu_robot_interfaces::msg::GripperCommand_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<snu_robot_interfaces::msg::GripperCommand_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      snu_robot_interfaces::msg::GripperCommand_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<snu_robot_interfaces::msg::GripperCommand_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<snu_robot_interfaces::msg::GripperCommand_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<snu_robot_interfaces::msg::GripperCommand_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__snu_robot_interfaces__msg__GripperCommand
    std::shared_ptr<snu_robot_interfaces::msg::GripperCommand_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__snu_robot_interfaces__msg__GripperCommand
    std::shared_ptr<snu_robot_interfaces::msg::GripperCommand_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GripperCommand_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->command != other.command) {
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
  bool operator!=(const GripperCommand_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GripperCommand_

// alias to use template instance with default allocator
using GripperCommand =
  snu_robot_interfaces::msg::GripperCommand_<std::allocator<void>>;

// constant definitions
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t GripperCommand_<ContainerAllocator>::OPEN;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t GripperCommand_<ContainerAllocator>::CLOSE;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t GripperCommand_<ContainerAllocator>::STOP;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t GripperCommand_<ContainerAllocator>::SET_OPENING;
#endif  // __cplusplus < 201703L

}  // namespace msg

}  // namespace snu_robot_interfaces

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__GRIPPER_COMMAND__STRUCT_HPP_
