// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from gesture_management:srv/PlaySequence.idl
// generated code does not contain a copyright notice

#ifndef GESTURE_MANAGEMENT__SRV__DETAIL__PLAY_SEQUENCE__STRUCT_HPP_
#define GESTURE_MANAGEMENT__SRV__DETAIL__PLAY_SEQUENCE__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__gesture_management__srv__PlaySequence_Request __attribute__((deprecated))
#else
# define DEPRECATED__gesture_management__srv__PlaySequence_Request __declspec(deprecated)
#endif

namespace gesture_management
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct PlaySequence_Request_
{
  using Type = PlaySequence_Request_<ContainerAllocator>;

  explicit PlaySequence_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->sequence_name = "";
      this->output_topic = "";
      this->replay_speed = 0.0f;
      this->repeat_mode = "";
      this->repeat_count = 0l;
      this->interval_s = 0.0f;
    }
  }

  explicit PlaySequence_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : sequence_name(_alloc),
    output_topic(_alloc),
    repeat_mode(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->sequence_name = "";
      this->output_topic = "";
      this->replay_speed = 0.0f;
      this->repeat_mode = "";
      this->repeat_count = 0l;
      this->interval_s = 0.0f;
    }
  }

  // field types and members
  using _sequence_name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _sequence_name_type sequence_name;
  using _recording_names_type =
    std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>>;
  _recording_names_type recording_names;
  using _output_topic_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _output_topic_type output_topic;
  using _replay_speed_type =
    float;
  _replay_speed_type replay_speed;
  using _repeat_mode_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _repeat_mode_type repeat_mode;
  using _repeat_count_type =
    int32_t;
  _repeat_count_type repeat_count;
  using _interval_s_type =
    float;
  _interval_s_type interval_s;

  // setters for named parameter idiom
  Type & set__sequence_name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->sequence_name = _arg;
    return *this;
  }
  Type & set__recording_names(
    const std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>> & _arg)
  {
    this->recording_names = _arg;
    return *this;
  }
  Type & set__output_topic(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->output_topic = _arg;
    return *this;
  }
  Type & set__replay_speed(
    const float & _arg)
  {
    this->replay_speed = _arg;
    return *this;
  }
  Type & set__repeat_mode(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->repeat_mode = _arg;
    return *this;
  }
  Type & set__repeat_count(
    const int32_t & _arg)
  {
    this->repeat_count = _arg;
    return *this;
  }
  Type & set__interval_s(
    const float & _arg)
  {
    this->interval_s = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    gesture_management::srv::PlaySequence_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const gesture_management::srv::PlaySequence_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<gesture_management::srv::PlaySequence_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<gesture_management::srv::PlaySequence_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      gesture_management::srv::PlaySequence_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<gesture_management::srv::PlaySequence_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      gesture_management::srv::PlaySequence_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<gesture_management::srv::PlaySequence_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<gesture_management::srv::PlaySequence_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<gesture_management::srv::PlaySequence_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__gesture_management__srv__PlaySequence_Request
    std::shared_ptr<gesture_management::srv::PlaySequence_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__gesture_management__srv__PlaySequence_Request
    std::shared_ptr<gesture_management::srv::PlaySequence_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const PlaySequence_Request_ & other) const
  {
    if (this->sequence_name != other.sequence_name) {
      return false;
    }
    if (this->recording_names != other.recording_names) {
      return false;
    }
    if (this->output_topic != other.output_topic) {
      return false;
    }
    if (this->replay_speed != other.replay_speed) {
      return false;
    }
    if (this->repeat_mode != other.repeat_mode) {
      return false;
    }
    if (this->repeat_count != other.repeat_count) {
      return false;
    }
    if (this->interval_s != other.interval_s) {
      return false;
    }
    return true;
  }
  bool operator!=(const PlaySequence_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct PlaySequence_Request_

// alias to use template instance with default allocator
using PlaySequence_Request =
  gesture_management::srv::PlaySequence_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace gesture_management


#ifndef _WIN32
# define DEPRECATED__gesture_management__srv__PlaySequence_Response __attribute__((deprecated))
#else
# define DEPRECATED__gesture_management__srv__PlaySequence_Response __declspec(deprecated)
#endif

namespace gesture_management
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct PlaySequence_Response_
{
  using Type = PlaySequence_Response_<ContainerAllocator>;

  explicit PlaySequence_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->message = "";
    }
  }

  explicit PlaySequence_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
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
    gesture_management::srv::PlaySequence_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const gesture_management::srv::PlaySequence_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<gesture_management::srv::PlaySequence_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<gesture_management::srv::PlaySequence_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      gesture_management::srv::PlaySequence_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<gesture_management::srv::PlaySequence_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      gesture_management::srv::PlaySequence_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<gesture_management::srv::PlaySequence_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<gesture_management::srv::PlaySequence_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<gesture_management::srv::PlaySequence_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__gesture_management__srv__PlaySequence_Response
    std::shared_ptr<gesture_management::srv::PlaySequence_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__gesture_management__srv__PlaySequence_Response
    std::shared_ptr<gesture_management::srv::PlaySequence_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const PlaySequence_Response_ & other) const
  {
    if (this->success != other.success) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const PlaySequence_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct PlaySequence_Response_

// alias to use template instance with default allocator
using PlaySequence_Response =
  gesture_management::srv::PlaySequence_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace gesture_management

namespace gesture_management
{

namespace srv
{

struct PlaySequence
{
  using Request = gesture_management::srv::PlaySequence_Request;
  using Response = gesture_management::srv::PlaySequence_Response;
};

}  // namespace srv

}  // namespace gesture_management

#endif  // GESTURE_MANAGEMENT__SRV__DETAIL__PLAY_SEQUENCE__STRUCT_HPP_
