// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from daksha_msgs:srv/StartReplay.idl
// generated code does not contain a copyright notice

#ifndef DAKSHA_MSGS__SRV__DETAIL__START_REPLAY__STRUCT_HPP_
#define DAKSHA_MSGS__SRV__DETAIL__START_REPLAY__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__daksha_msgs__srv__StartReplay_Request __attribute__((deprecated))
#else
# define DEPRECATED__daksha_msgs__srv__StartReplay_Request __declspec(deprecated)
#endif

namespace daksha_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct StartReplay_Request_
{
  using Type = StartReplay_Request_<ContainerAllocator>;

  explicit StartReplay_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->dataset_name = "";
      this->episode_index = 0l;
      this->speed = 0.0f;
    }
  }

  explicit StartReplay_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : dataset_name(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->dataset_name = "";
      this->episode_index = 0l;
      this->speed = 0.0f;
    }
  }

  // field types and members
  using _dataset_name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _dataset_name_type dataset_name;
  using _episode_index_type =
    int32_t;
  _episode_index_type episode_index;
  using _speed_type =
    float;
  _speed_type speed;

  // setters for named parameter idiom
  Type & set__dataset_name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->dataset_name = _arg;
    return *this;
  }
  Type & set__episode_index(
    const int32_t & _arg)
  {
    this->episode_index = _arg;
    return *this;
  }
  Type & set__speed(
    const float & _arg)
  {
    this->speed = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    daksha_msgs::srv::StartReplay_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const daksha_msgs::srv::StartReplay_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<daksha_msgs::srv::StartReplay_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<daksha_msgs::srv::StartReplay_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      daksha_msgs::srv::StartReplay_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<daksha_msgs::srv::StartReplay_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      daksha_msgs::srv::StartReplay_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<daksha_msgs::srv::StartReplay_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<daksha_msgs::srv::StartReplay_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<daksha_msgs::srv::StartReplay_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__daksha_msgs__srv__StartReplay_Request
    std::shared_ptr<daksha_msgs::srv::StartReplay_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__daksha_msgs__srv__StartReplay_Request
    std::shared_ptr<daksha_msgs::srv::StartReplay_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const StartReplay_Request_ & other) const
  {
    if (this->dataset_name != other.dataset_name) {
      return false;
    }
    if (this->episode_index != other.episode_index) {
      return false;
    }
    if (this->speed != other.speed) {
      return false;
    }
    return true;
  }
  bool operator!=(const StartReplay_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct StartReplay_Request_

// alias to use template instance with default allocator
using StartReplay_Request =
  daksha_msgs::srv::StartReplay_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace daksha_msgs


#ifndef _WIN32
# define DEPRECATED__daksha_msgs__srv__StartReplay_Response __attribute__((deprecated))
#else
# define DEPRECATED__daksha_msgs__srv__StartReplay_Response __declspec(deprecated)
#endif

namespace daksha_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct StartReplay_Response_
{
  using Type = StartReplay_Response_<ContainerAllocator>;

  explicit StartReplay_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->message = "";
    }
  }

  explicit StartReplay_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
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
    daksha_msgs::srv::StartReplay_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const daksha_msgs::srv::StartReplay_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<daksha_msgs::srv::StartReplay_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<daksha_msgs::srv::StartReplay_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      daksha_msgs::srv::StartReplay_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<daksha_msgs::srv::StartReplay_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      daksha_msgs::srv::StartReplay_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<daksha_msgs::srv::StartReplay_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<daksha_msgs::srv::StartReplay_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<daksha_msgs::srv::StartReplay_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__daksha_msgs__srv__StartReplay_Response
    std::shared_ptr<daksha_msgs::srv::StartReplay_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__daksha_msgs__srv__StartReplay_Response
    std::shared_ptr<daksha_msgs::srv::StartReplay_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const StartReplay_Response_ & other) const
  {
    if (this->success != other.success) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const StartReplay_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct StartReplay_Response_

// alias to use template instance with default allocator
using StartReplay_Response =
  daksha_msgs::srv::StartReplay_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace daksha_msgs

namespace daksha_msgs
{

namespace srv
{

struct StartReplay
{
  using Request = daksha_msgs::srv::StartReplay_Request;
  using Response = daksha_msgs::srv::StartReplay_Response;
};

}  // namespace srv

}  // namespace daksha_msgs

#endif  // DAKSHA_MSGS__SRV__DETAIL__START_REPLAY__STRUCT_HPP_
