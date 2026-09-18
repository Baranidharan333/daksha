// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from gesture_management:srv/ListSequences.idl
// generated code does not contain a copyright notice

#ifndef GESTURE_MANAGEMENT__SRV__DETAIL__LIST_SEQUENCES__STRUCT_HPP_
#define GESTURE_MANAGEMENT__SRV__DETAIL__LIST_SEQUENCES__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__gesture_management__srv__ListSequences_Request __attribute__((deprecated))
#else
# define DEPRECATED__gesture_management__srv__ListSequences_Request __declspec(deprecated)
#endif

namespace gesture_management
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct ListSequences_Request_
{
  using Type = ListSequences_Request_<ContainerAllocator>;

  explicit ListSequences_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  explicit ListSequences_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  // field types and members
  using _structure_needs_at_least_one_member_type =
    uint8_t;
  _structure_needs_at_least_one_member_type structure_needs_at_least_one_member;


  // constant declarations

  // pointer types
  using RawPtr =
    gesture_management::srv::ListSequences_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const gesture_management::srv::ListSequences_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<gesture_management::srv::ListSequences_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<gesture_management::srv::ListSequences_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      gesture_management::srv::ListSequences_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<gesture_management::srv::ListSequences_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      gesture_management::srv::ListSequences_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<gesture_management::srv::ListSequences_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<gesture_management::srv::ListSequences_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<gesture_management::srv::ListSequences_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__gesture_management__srv__ListSequences_Request
    std::shared_ptr<gesture_management::srv::ListSequences_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__gesture_management__srv__ListSequences_Request
    std::shared_ptr<gesture_management::srv::ListSequences_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ListSequences_Request_ & other) const
  {
    if (this->structure_needs_at_least_one_member != other.structure_needs_at_least_one_member) {
      return false;
    }
    return true;
  }
  bool operator!=(const ListSequences_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ListSequences_Request_

// alias to use template instance with default allocator
using ListSequences_Request =
  gesture_management::srv::ListSequences_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace gesture_management


#ifndef _WIN32
# define DEPRECATED__gesture_management__srv__ListSequences_Response __attribute__((deprecated))
#else
# define DEPRECATED__gesture_management__srv__ListSequences_Response __declspec(deprecated)
#endif

namespace gesture_management
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct ListSequences_Response_
{
  using Type = ListSequences_Response_<ContainerAllocator>;

  explicit ListSequences_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->sequences_json = "";
    }
  }

  explicit ListSequences_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : sequences_json(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->sequences_json = "";
    }
  }

  // field types and members
  using _success_type =
    bool;
  _success_type success;
  using _sequences_json_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _sequences_json_type sequences_json;

  // setters for named parameter idiom
  Type & set__success(
    const bool & _arg)
  {
    this->success = _arg;
    return *this;
  }
  Type & set__sequences_json(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->sequences_json = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    gesture_management::srv::ListSequences_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const gesture_management::srv::ListSequences_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<gesture_management::srv::ListSequences_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<gesture_management::srv::ListSequences_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      gesture_management::srv::ListSequences_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<gesture_management::srv::ListSequences_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      gesture_management::srv::ListSequences_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<gesture_management::srv::ListSequences_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<gesture_management::srv::ListSequences_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<gesture_management::srv::ListSequences_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__gesture_management__srv__ListSequences_Response
    std::shared_ptr<gesture_management::srv::ListSequences_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__gesture_management__srv__ListSequences_Response
    std::shared_ptr<gesture_management::srv::ListSequences_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ListSequences_Response_ & other) const
  {
    if (this->success != other.success) {
      return false;
    }
    if (this->sequences_json != other.sequences_json) {
      return false;
    }
    return true;
  }
  bool operator!=(const ListSequences_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ListSequences_Response_

// alias to use template instance with default allocator
using ListSequences_Response =
  gesture_management::srv::ListSequences_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace gesture_management

namespace gesture_management
{

namespace srv
{

struct ListSequences
{
  using Request = gesture_management::srv::ListSequences_Request;
  using Response = gesture_management::srv::ListSequences_Response;
};

}  // namespace srv

}  // namespace gesture_management

#endif  // GESTURE_MANAGEMENT__SRV__DETAIL__LIST_SEQUENCES__STRUCT_HPP_
