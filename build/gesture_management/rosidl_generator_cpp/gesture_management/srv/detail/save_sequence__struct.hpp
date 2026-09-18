// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from gesture_management:srv/SaveSequence.idl
// generated code does not contain a copyright notice

#ifndef GESTURE_MANAGEMENT__SRV__DETAIL__SAVE_SEQUENCE__STRUCT_HPP_
#define GESTURE_MANAGEMENT__SRV__DETAIL__SAVE_SEQUENCE__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__gesture_management__srv__SaveSequence_Request __attribute__((deprecated))
#else
# define DEPRECATED__gesture_management__srv__SaveSequence_Request __declspec(deprecated)
#endif

namespace gesture_management
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct SaveSequence_Request_
{
  using Type = SaveSequence_Request_<ContainerAllocator>;

  explicit SaveSequence_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->name = "";
    }
  }

  explicit SaveSequence_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : name(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->name = "";
    }
  }

  // field types and members
  using _name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _name_type name;
  using _recording_names_type =
    std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>>;
  _recording_names_type recording_names;

  // setters for named parameter idiom
  Type & set__name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->name = _arg;
    return *this;
  }
  Type & set__recording_names(
    const std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>> & _arg)
  {
    this->recording_names = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    gesture_management::srv::SaveSequence_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const gesture_management::srv::SaveSequence_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<gesture_management::srv::SaveSequence_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<gesture_management::srv::SaveSequence_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      gesture_management::srv::SaveSequence_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<gesture_management::srv::SaveSequence_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      gesture_management::srv::SaveSequence_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<gesture_management::srv::SaveSequence_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<gesture_management::srv::SaveSequence_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<gesture_management::srv::SaveSequence_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__gesture_management__srv__SaveSequence_Request
    std::shared_ptr<gesture_management::srv::SaveSequence_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__gesture_management__srv__SaveSequence_Request
    std::shared_ptr<gesture_management::srv::SaveSequence_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const SaveSequence_Request_ & other) const
  {
    if (this->name != other.name) {
      return false;
    }
    if (this->recording_names != other.recording_names) {
      return false;
    }
    return true;
  }
  bool operator!=(const SaveSequence_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct SaveSequence_Request_

// alias to use template instance with default allocator
using SaveSequence_Request =
  gesture_management::srv::SaveSequence_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace gesture_management


#ifndef _WIN32
# define DEPRECATED__gesture_management__srv__SaveSequence_Response __attribute__((deprecated))
#else
# define DEPRECATED__gesture_management__srv__SaveSequence_Response __declspec(deprecated)
#endif

namespace gesture_management
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct SaveSequence_Response_
{
  using Type = SaveSequence_Response_<ContainerAllocator>;

  explicit SaveSequence_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->message = "";
    }
  }

  explicit SaveSequence_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
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
    gesture_management::srv::SaveSequence_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const gesture_management::srv::SaveSequence_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<gesture_management::srv::SaveSequence_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<gesture_management::srv::SaveSequence_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      gesture_management::srv::SaveSequence_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<gesture_management::srv::SaveSequence_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      gesture_management::srv::SaveSequence_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<gesture_management::srv::SaveSequence_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<gesture_management::srv::SaveSequence_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<gesture_management::srv::SaveSequence_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__gesture_management__srv__SaveSequence_Response
    std::shared_ptr<gesture_management::srv::SaveSequence_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__gesture_management__srv__SaveSequence_Response
    std::shared_ptr<gesture_management::srv::SaveSequence_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const SaveSequence_Response_ & other) const
  {
    if (this->success != other.success) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const SaveSequence_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct SaveSequence_Response_

// alias to use template instance with default allocator
using SaveSequence_Response =
  gesture_management::srv::SaveSequence_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace gesture_management

namespace gesture_management
{

namespace srv
{

struct SaveSequence
{
  using Request = gesture_management::srv::SaveSequence_Request;
  using Response = gesture_management::srv::SaveSequence_Response;
};

}  // namespace srv

}  // namespace gesture_management

#endif  // GESTURE_MANAGEMENT__SRV__DETAIL__SAVE_SEQUENCE__STRUCT_HPP_
