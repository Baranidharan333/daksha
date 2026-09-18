// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from collision_management:srv/GetCollisionStatus.idl
// generated code does not contain a copyright notice

#ifndef COLLISION_MANAGEMENT__SRV__DETAIL__GET_COLLISION_STATUS__STRUCT_HPP_
#define COLLISION_MANAGEMENT__SRV__DETAIL__GET_COLLISION_STATUS__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__collision_management__srv__GetCollisionStatus_Request __attribute__((deprecated))
#else
# define DEPRECATED__collision_management__srv__GetCollisionStatus_Request __declspec(deprecated)
#endif

namespace collision_management
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct GetCollisionStatus_Request_
{
  using Type = GetCollisionStatus_Request_<ContainerAllocator>;

  explicit GetCollisionStatus_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  explicit GetCollisionStatus_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
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
    collision_management::srv::GetCollisionStatus_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const collision_management::srv::GetCollisionStatus_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<collision_management::srv::GetCollisionStatus_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<collision_management::srv::GetCollisionStatus_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      collision_management::srv::GetCollisionStatus_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<collision_management::srv::GetCollisionStatus_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      collision_management::srv::GetCollisionStatus_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<collision_management::srv::GetCollisionStatus_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<collision_management::srv::GetCollisionStatus_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<collision_management::srv::GetCollisionStatus_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__collision_management__srv__GetCollisionStatus_Request
    std::shared_ptr<collision_management::srv::GetCollisionStatus_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__collision_management__srv__GetCollisionStatus_Request
    std::shared_ptr<collision_management::srv::GetCollisionStatus_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GetCollisionStatus_Request_ & other) const
  {
    if (this->structure_needs_at_least_one_member != other.structure_needs_at_least_one_member) {
      return false;
    }
    return true;
  }
  bool operator!=(const GetCollisionStatus_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GetCollisionStatus_Request_

// alias to use template instance with default allocator
using GetCollisionStatus_Request =
  collision_management::srv::GetCollisionStatus_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace collision_management


// Include directives for member types
// Member 'status'
#include "sensor_msgs/msg/detail/joint_state__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__collision_management__srv__GetCollisionStatus_Response __attribute__((deprecated))
#else
# define DEPRECATED__collision_management__srv__GetCollisionStatus_Response __declspec(deprecated)
#endif

namespace collision_management
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct GetCollisionStatus_Response_
{
  using Type = GetCollisionStatus_Response_<ContainerAllocator>;

  explicit GetCollisionStatus_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : status(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->in_collision = false;
    }
  }

  explicit GetCollisionStatus_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : status(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->in_collision = false;
    }
  }

  // field types and members
  using _in_collision_type =
    bool;
  _in_collision_type in_collision;
  using _status_type =
    sensor_msgs::msg::JointState_<ContainerAllocator>;
  _status_type status;

  // setters for named parameter idiom
  Type & set__in_collision(
    const bool & _arg)
  {
    this->in_collision = _arg;
    return *this;
  }
  Type & set__status(
    const sensor_msgs::msg::JointState_<ContainerAllocator> & _arg)
  {
    this->status = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    collision_management::srv::GetCollisionStatus_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const collision_management::srv::GetCollisionStatus_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<collision_management::srv::GetCollisionStatus_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<collision_management::srv::GetCollisionStatus_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      collision_management::srv::GetCollisionStatus_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<collision_management::srv::GetCollisionStatus_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      collision_management::srv::GetCollisionStatus_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<collision_management::srv::GetCollisionStatus_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<collision_management::srv::GetCollisionStatus_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<collision_management::srv::GetCollisionStatus_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__collision_management__srv__GetCollisionStatus_Response
    std::shared_ptr<collision_management::srv::GetCollisionStatus_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__collision_management__srv__GetCollisionStatus_Response
    std::shared_ptr<collision_management::srv::GetCollisionStatus_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GetCollisionStatus_Response_ & other) const
  {
    if (this->in_collision != other.in_collision) {
      return false;
    }
    if (this->status != other.status) {
      return false;
    }
    return true;
  }
  bool operator!=(const GetCollisionStatus_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GetCollisionStatus_Response_

// alias to use template instance with default allocator
using GetCollisionStatus_Response =
  collision_management::srv::GetCollisionStatus_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace collision_management

namespace collision_management
{

namespace srv
{

struct GetCollisionStatus
{
  using Request = collision_management::srv::GetCollisionStatus_Request;
  using Response = collision_management::srv::GetCollisionStatus_Response;
};

}  // namespace srv

}  // namespace collision_management

#endif  // COLLISION_MANAGEMENT__SRV__DETAIL__GET_COLLISION_STATUS__STRUCT_HPP_
