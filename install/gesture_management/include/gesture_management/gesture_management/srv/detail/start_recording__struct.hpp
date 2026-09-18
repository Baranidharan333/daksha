// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from gesture_management:srv/StartRecording.idl
// generated code does not contain a copyright notice

#ifndef GESTURE_MANAGEMENT__SRV__DETAIL__START_RECORDING__STRUCT_HPP_
#define GESTURE_MANAGEMENT__SRV__DETAIL__START_RECORDING__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__gesture_management__srv__StartRecording_Request __attribute__((deprecated))
#else
# define DEPRECATED__gesture_management__srv__StartRecording_Request __declspec(deprecated)
#endif

namespace gesture_management
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct StartRecording_Request_
{
  using Type = StartRecording_Request_<ContainerAllocator>;

  explicit StartRecording_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->topic_name = "";
      this->recording_name = "";
      this->action = "";
    }
  }

  explicit StartRecording_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : topic_name(_alloc),
    recording_name(_alloc),
    action(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->topic_name = "";
      this->recording_name = "";
      this->action = "";
    }
  }

  // field types and members
  using _topic_name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _topic_name_type topic_name;
  using _recording_name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _recording_name_type recording_name;
  using _action_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _action_type action;

  // setters for named parameter idiom
  Type & set__topic_name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->topic_name = _arg;
    return *this;
  }
  Type & set__recording_name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->recording_name = _arg;
    return *this;
  }
  Type & set__action(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->action = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    gesture_management::srv::StartRecording_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const gesture_management::srv::StartRecording_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<gesture_management::srv::StartRecording_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<gesture_management::srv::StartRecording_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      gesture_management::srv::StartRecording_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<gesture_management::srv::StartRecording_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      gesture_management::srv::StartRecording_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<gesture_management::srv::StartRecording_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<gesture_management::srv::StartRecording_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<gesture_management::srv::StartRecording_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__gesture_management__srv__StartRecording_Request
    std::shared_ptr<gesture_management::srv::StartRecording_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__gesture_management__srv__StartRecording_Request
    std::shared_ptr<gesture_management::srv::StartRecording_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const StartRecording_Request_ & other) const
  {
    if (this->topic_name != other.topic_name) {
      return false;
    }
    if (this->recording_name != other.recording_name) {
      return false;
    }
    if (this->action != other.action) {
      return false;
    }
    return true;
  }
  bool operator!=(const StartRecording_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct StartRecording_Request_

// alias to use template instance with default allocator
using StartRecording_Request =
  gesture_management::srv::StartRecording_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace gesture_management


#ifndef _WIN32
# define DEPRECATED__gesture_management__srv__StartRecording_Response __attribute__((deprecated))
#else
# define DEPRECATED__gesture_management__srv__StartRecording_Response __declspec(deprecated)
#endif

namespace gesture_management
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct StartRecording_Response_
{
  using Type = StartRecording_Response_<ContainerAllocator>;

  explicit StartRecording_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->message = "";
    }
  }

  explicit StartRecording_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
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
    gesture_management::srv::StartRecording_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const gesture_management::srv::StartRecording_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<gesture_management::srv::StartRecording_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<gesture_management::srv::StartRecording_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      gesture_management::srv::StartRecording_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<gesture_management::srv::StartRecording_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      gesture_management::srv::StartRecording_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<gesture_management::srv::StartRecording_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<gesture_management::srv::StartRecording_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<gesture_management::srv::StartRecording_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__gesture_management__srv__StartRecording_Response
    std::shared_ptr<gesture_management::srv::StartRecording_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__gesture_management__srv__StartRecording_Response
    std::shared_ptr<gesture_management::srv::StartRecording_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const StartRecording_Response_ & other) const
  {
    if (this->success != other.success) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const StartRecording_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct StartRecording_Response_

// alias to use template instance with default allocator
using StartRecording_Response =
  gesture_management::srv::StartRecording_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace gesture_management

namespace gesture_management
{

namespace srv
{

struct StartRecording
{
  using Request = gesture_management::srv::StartRecording_Request;
  using Response = gesture_management::srv::StartRecording_Response;
};

}  // namespace srv

}  // namespace gesture_management

#endif  // GESTURE_MANAGEMENT__SRV__DETAIL__START_RECORDING__STRUCT_HPP_
