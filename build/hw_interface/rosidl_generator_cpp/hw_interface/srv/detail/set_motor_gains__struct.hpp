// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from hw_interface:srv/SetMotorGains.idl
// generated code does not contain a copyright notice

#ifndef HW_INTERFACE__SRV__DETAIL__SET_MOTOR_GAINS__STRUCT_HPP_
#define HW_INTERFACE__SRV__DETAIL__SET_MOTOR_GAINS__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__hw_interface__srv__SetMotorGains_Request __attribute__((deprecated))
#else
# define DEPRECATED__hw_interface__srv__SetMotorGains_Request __declspec(deprecated)
#endif

namespace hw_interface
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct SetMotorGains_Request_
{
  using Type = SetMotorGains_Request_<ContainerAllocator>;

  explicit SetMotorGains_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_init;
  }

  explicit SetMotorGains_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_init;
    (void)_alloc;
  }

  // field types and members
  using _motor_ids_type =
    std::vector<int32_t, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<int32_t>>;
  _motor_ids_type motor_ids;
  using _kp_type =
    std::vector<float, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<float>>;
  _kp_type kp;
  using _kd_type =
    std::vector<float, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<float>>;
  _kd_type kd;

  // setters for named parameter idiom
  Type & set__motor_ids(
    const std::vector<int32_t, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<int32_t>> & _arg)
  {
    this->motor_ids = _arg;
    return *this;
  }
  Type & set__kp(
    const std::vector<float, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<float>> & _arg)
  {
    this->kp = _arg;
    return *this;
  }
  Type & set__kd(
    const std::vector<float, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<float>> & _arg)
  {
    this->kd = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    hw_interface::srv::SetMotorGains_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const hw_interface::srv::SetMotorGains_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<hw_interface::srv::SetMotorGains_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<hw_interface::srv::SetMotorGains_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      hw_interface::srv::SetMotorGains_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<hw_interface::srv::SetMotorGains_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      hw_interface::srv::SetMotorGains_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<hw_interface::srv::SetMotorGains_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<hw_interface::srv::SetMotorGains_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<hw_interface::srv::SetMotorGains_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__hw_interface__srv__SetMotorGains_Request
    std::shared_ptr<hw_interface::srv::SetMotorGains_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__hw_interface__srv__SetMotorGains_Request
    std::shared_ptr<hw_interface::srv::SetMotorGains_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const SetMotorGains_Request_ & other) const
  {
    if (this->motor_ids != other.motor_ids) {
      return false;
    }
    if (this->kp != other.kp) {
      return false;
    }
    if (this->kd != other.kd) {
      return false;
    }
    return true;
  }
  bool operator!=(const SetMotorGains_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct SetMotorGains_Request_

// alias to use template instance with default allocator
using SetMotorGains_Request =
  hw_interface::srv::SetMotorGains_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace hw_interface


#ifndef _WIN32
# define DEPRECATED__hw_interface__srv__SetMotorGains_Response __attribute__((deprecated))
#else
# define DEPRECATED__hw_interface__srv__SetMotorGains_Response __declspec(deprecated)
#endif

namespace hw_interface
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct SetMotorGains_Response_
{
  using Type = SetMotorGains_Response_<ContainerAllocator>;

  explicit SetMotorGains_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->message = "";
    }
  }

  explicit SetMotorGains_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : message(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->message = "";
    }
  }

  // field types and members
  using _success_type =
    bool;
  _success_type success;
  using _message_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _message_type message;

  // setters for named parameter idiom
  Type & set__success(
    const bool & _arg)
  {
    this->success = _arg;
    return *this;
  }
  Type & set__message(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->message = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    hw_interface::srv::SetMotorGains_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const hw_interface::srv::SetMotorGains_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<hw_interface::srv::SetMotorGains_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<hw_interface::srv::SetMotorGains_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      hw_interface::srv::SetMotorGains_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<hw_interface::srv::SetMotorGains_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      hw_interface::srv::SetMotorGains_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<hw_interface::srv::SetMotorGains_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<hw_interface::srv::SetMotorGains_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<hw_interface::srv::SetMotorGains_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__hw_interface__srv__SetMotorGains_Response
    std::shared_ptr<hw_interface::srv::SetMotorGains_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__hw_interface__srv__SetMotorGains_Response
    std::shared_ptr<hw_interface::srv::SetMotorGains_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const SetMotorGains_Response_ & other) const
  {
    if (this->success != other.success) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const SetMotorGains_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct SetMotorGains_Response_

// alias to use template instance with default allocator
using SetMotorGains_Response =
  hw_interface::srv::SetMotorGains_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace hw_interface

namespace hw_interface
{

namespace srv
{

struct SetMotorGains
{
  using Request = hw_interface::srv::SetMotorGains_Request;
  using Response = hw_interface::srv::SetMotorGains_Response;
};

}  // namespace srv

}  // namespace hw_interface

#endif  // HW_INTERFACE__SRV__DETAIL__SET_MOTOR_GAINS__STRUCT_HPP_
