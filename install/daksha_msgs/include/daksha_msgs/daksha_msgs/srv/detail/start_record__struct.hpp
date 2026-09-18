// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from daksha_msgs:srv/StartRecord.idl
// generated code does not contain a copyright notice

#ifndef DAKSHA_MSGS__SRV__DETAIL__START_RECORD__STRUCT_HPP_
#define DAKSHA_MSGS__SRV__DETAIL__START_RECORD__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__daksha_msgs__srv__StartRecord_Request __attribute__((deprecated))
#else
# define DEPRECATED__daksha_msgs__srv__StartRecord_Request __declspec(deprecated)
#endif

namespace daksha_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct StartRecord_Request_
{
  using Type = StartRecord_Request_<ContainerAllocator>;

  explicit StartRecord_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->dataset_name = "";
      this->episode_length = 0l;
      this->record_hz = 0.0f;
      this->max_episodes = 0l;
    }
  }

  explicit StartRecord_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : dataset_name(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->dataset_name = "";
      this->episode_length = 0l;
      this->record_hz = 0.0f;
      this->max_episodes = 0l;
    }
  }

  // field types and members
  using _dataset_name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _dataset_name_type dataset_name;
  using _episode_length_type =
    int32_t;
  _episode_length_type episode_length;
  using _record_hz_type =
    float;
  _record_hz_type record_hz;
  using _max_episodes_type =
    int32_t;
  _max_episodes_type max_episodes;

  // setters for named parameter idiom
  Type & set__dataset_name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->dataset_name = _arg;
    return *this;
  }
  Type & set__episode_length(
    const int32_t & _arg)
  {
    this->episode_length = _arg;
    return *this;
  }
  Type & set__record_hz(
    const float & _arg)
  {
    this->record_hz = _arg;
    return *this;
  }
  Type & set__max_episodes(
    const int32_t & _arg)
  {
    this->max_episodes = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    daksha_msgs::srv::StartRecord_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const daksha_msgs::srv::StartRecord_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<daksha_msgs::srv::StartRecord_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<daksha_msgs::srv::StartRecord_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      daksha_msgs::srv::StartRecord_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<daksha_msgs::srv::StartRecord_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      daksha_msgs::srv::StartRecord_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<daksha_msgs::srv::StartRecord_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<daksha_msgs::srv::StartRecord_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<daksha_msgs::srv::StartRecord_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__daksha_msgs__srv__StartRecord_Request
    std::shared_ptr<daksha_msgs::srv::StartRecord_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__daksha_msgs__srv__StartRecord_Request
    std::shared_ptr<daksha_msgs::srv::StartRecord_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const StartRecord_Request_ & other) const
  {
    if (this->dataset_name != other.dataset_name) {
      return false;
    }
    if (this->episode_length != other.episode_length) {
      return false;
    }
    if (this->record_hz != other.record_hz) {
      return false;
    }
    if (this->max_episodes != other.max_episodes) {
      return false;
    }
    return true;
  }
  bool operator!=(const StartRecord_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct StartRecord_Request_

// alias to use template instance with default allocator
using StartRecord_Request =
  daksha_msgs::srv::StartRecord_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace daksha_msgs


#ifndef _WIN32
# define DEPRECATED__daksha_msgs__srv__StartRecord_Response __attribute__((deprecated))
#else
# define DEPRECATED__daksha_msgs__srv__StartRecord_Response __declspec(deprecated)
#endif

namespace daksha_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct StartRecord_Response_
{
  using Type = StartRecord_Response_<ContainerAllocator>;

  explicit StartRecord_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->message = "";
    }
  }

  explicit StartRecord_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
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
    daksha_msgs::srv::StartRecord_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const daksha_msgs::srv::StartRecord_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<daksha_msgs::srv::StartRecord_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<daksha_msgs::srv::StartRecord_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      daksha_msgs::srv::StartRecord_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<daksha_msgs::srv::StartRecord_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      daksha_msgs::srv::StartRecord_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<daksha_msgs::srv::StartRecord_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<daksha_msgs::srv::StartRecord_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<daksha_msgs::srv::StartRecord_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__daksha_msgs__srv__StartRecord_Response
    std::shared_ptr<daksha_msgs::srv::StartRecord_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__daksha_msgs__srv__StartRecord_Response
    std::shared_ptr<daksha_msgs::srv::StartRecord_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const StartRecord_Response_ & other) const
  {
    if (this->success != other.success) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const StartRecord_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct StartRecord_Response_

// alias to use template instance with default allocator
using StartRecord_Response =
  daksha_msgs::srv::StartRecord_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace daksha_msgs

namespace daksha_msgs
{

namespace srv
{

struct StartRecord
{
  using Request = daksha_msgs::srv::StartRecord_Request;
  using Response = daksha_msgs::srv::StartRecord_Response;
};

}  // namespace srv

}  // namespace daksha_msgs

#endif  // DAKSHA_MSGS__SRV__DETAIL__START_RECORD__STRUCT_HPP_
