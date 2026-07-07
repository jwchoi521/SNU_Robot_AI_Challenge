// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from snu_robot_interfaces:msg/DetectedTarget.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET__STRUCT_HPP_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__snu_robot_interfaces__msg__DetectedTarget __attribute__((deprecated))
#else
# define DEPRECATED__snu_robot_interfaces__msg__DetectedTarget __declspec(deprecated)
#endif

namespace snu_robot_interfaces
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct DetectedTarget_
{
  using Type = DetectedTarget_<ContainerAllocator>;

  explicit DetectedTarget_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->object_kind = "";
      this->fruit_kind = "";
      this->confidence = 0.0f;
      this->bbox_x1 = 0.0f;
      this->bbox_y1 = 0.0f;
      this->bbox_x2 = 0.0f;
      this->bbox_y2 = 0.0f;
      this->bearing_deg = 0.0f;
      this->has_distance = false;
      this->distance_m = 0.0f;
      this->pick_allowed = false;
      this->target_confirmed = false;
    }
  }

  explicit DetectedTarget_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : object_kind(_alloc),
    fruit_kind(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->object_kind = "";
      this->fruit_kind = "";
      this->confidence = 0.0f;
      this->bbox_x1 = 0.0f;
      this->bbox_y1 = 0.0f;
      this->bbox_x2 = 0.0f;
      this->bbox_y2 = 0.0f;
      this->bearing_deg = 0.0f;
      this->has_distance = false;
      this->distance_m = 0.0f;
      this->pick_allowed = false;
      this->target_confirmed = false;
    }
  }

  // field types and members
  using _object_kind_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _object_kind_type object_kind;
  using _fruit_kind_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _fruit_kind_type fruit_kind;
  using _confidence_type =
    float;
  _confidence_type confidence;
  using _bbox_x1_type =
    float;
  _bbox_x1_type bbox_x1;
  using _bbox_y1_type =
    float;
  _bbox_y1_type bbox_y1;
  using _bbox_x2_type =
    float;
  _bbox_x2_type bbox_x2;
  using _bbox_y2_type =
    float;
  _bbox_y2_type bbox_y2;
  using _bearing_deg_type =
    float;
  _bearing_deg_type bearing_deg;
  using _has_distance_type =
    bool;
  _has_distance_type has_distance;
  using _distance_m_type =
    float;
  _distance_m_type distance_m;
  using _pick_allowed_type =
    bool;
  _pick_allowed_type pick_allowed;
  using _target_confirmed_type =
    bool;
  _target_confirmed_type target_confirmed;

  // setters for named parameter idiom
  Type & set__object_kind(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->object_kind = _arg;
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
  Type & set__bbox_x1(
    const float & _arg)
  {
    this->bbox_x1 = _arg;
    return *this;
  }
  Type & set__bbox_y1(
    const float & _arg)
  {
    this->bbox_y1 = _arg;
    return *this;
  }
  Type & set__bbox_x2(
    const float & _arg)
  {
    this->bbox_x2 = _arg;
    return *this;
  }
  Type & set__bbox_y2(
    const float & _arg)
  {
    this->bbox_y2 = _arg;
    return *this;
  }
  Type & set__bearing_deg(
    const float & _arg)
  {
    this->bearing_deg = _arg;
    return *this;
  }
  Type & set__has_distance(
    const bool & _arg)
  {
    this->has_distance = _arg;
    return *this;
  }
  Type & set__distance_m(
    const float & _arg)
  {
    this->distance_m = _arg;
    return *this;
  }
  Type & set__pick_allowed(
    const bool & _arg)
  {
    this->pick_allowed = _arg;
    return *this;
  }
  Type & set__target_confirmed(
    const bool & _arg)
  {
    this->target_confirmed = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    snu_robot_interfaces::msg::DetectedTarget_<ContainerAllocator> *;
  using ConstRawPtr =
    const snu_robot_interfaces::msg::DetectedTarget_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<snu_robot_interfaces::msg::DetectedTarget_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<snu_robot_interfaces::msg::DetectedTarget_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      snu_robot_interfaces::msg::DetectedTarget_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<snu_robot_interfaces::msg::DetectedTarget_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      snu_robot_interfaces::msg::DetectedTarget_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<snu_robot_interfaces::msg::DetectedTarget_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<snu_robot_interfaces::msg::DetectedTarget_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<snu_robot_interfaces::msg::DetectedTarget_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__snu_robot_interfaces__msg__DetectedTarget
    std::shared_ptr<snu_robot_interfaces::msg::DetectedTarget_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__snu_robot_interfaces__msg__DetectedTarget
    std::shared_ptr<snu_robot_interfaces::msg::DetectedTarget_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const DetectedTarget_ & other) const
  {
    if (this->object_kind != other.object_kind) {
      return false;
    }
    if (this->fruit_kind != other.fruit_kind) {
      return false;
    }
    if (this->confidence != other.confidence) {
      return false;
    }
    if (this->bbox_x1 != other.bbox_x1) {
      return false;
    }
    if (this->bbox_y1 != other.bbox_y1) {
      return false;
    }
    if (this->bbox_x2 != other.bbox_x2) {
      return false;
    }
    if (this->bbox_y2 != other.bbox_y2) {
      return false;
    }
    if (this->bearing_deg != other.bearing_deg) {
      return false;
    }
    if (this->has_distance != other.has_distance) {
      return false;
    }
    if (this->distance_m != other.distance_m) {
      return false;
    }
    if (this->pick_allowed != other.pick_allowed) {
      return false;
    }
    if (this->target_confirmed != other.target_confirmed) {
      return false;
    }
    return true;
  }
  bool operator!=(const DetectedTarget_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct DetectedTarget_

// alias to use template instance with default allocator
using DetectedTarget =
  snu_robot_interfaces::msg::DetectedTarget_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace snu_robot_interfaces

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__DETECTED_TARGET__STRUCT_HPP_
