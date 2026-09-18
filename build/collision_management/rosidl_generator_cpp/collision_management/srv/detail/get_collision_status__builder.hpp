// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from collision_management:srv/GetCollisionStatus.idl
// generated code does not contain a copyright notice

#ifndef COLLISION_MANAGEMENT__SRV__DETAIL__GET_COLLISION_STATUS__BUILDER_HPP_
#define COLLISION_MANAGEMENT__SRV__DETAIL__GET_COLLISION_STATUS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "collision_management/srv/detail/get_collision_status__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace collision_management
{

namespace srv
{


}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::collision_management::srv::GetCollisionStatus_Request>()
{
  return ::collision_management::srv::GetCollisionStatus_Request(rosidl_runtime_cpp::MessageInitialization::ZERO);
}

}  // namespace collision_management


namespace collision_management
{

namespace srv
{

namespace builder
{

class Init_GetCollisionStatus_Response_status
{
public:
  explicit Init_GetCollisionStatus_Response_status(::collision_management::srv::GetCollisionStatus_Response & msg)
  : msg_(msg)
  {}
  ::collision_management::srv::GetCollisionStatus_Response status(::collision_management::srv::GetCollisionStatus_Response::_status_type arg)
  {
    msg_.status = std::move(arg);
    return std::move(msg_);
  }

private:
  ::collision_management::srv::GetCollisionStatus_Response msg_;
};

class Init_GetCollisionStatus_Response_in_collision
{
public:
  Init_GetCollisionStatus_Response_in_collision()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_GetCollisionStatus_Response_status in_collision(::collision_management::srv::GetCollisionStatus_Response::_in_collision_type arg)
  {
    msg_.in_collision = std::move(arg);
    return Init_GetCollisionStatus_Response_status(msg_);
  }

private:
  ::collision_management::srv::GetCollisionStatus_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::collision_management::srv::GetCollisionStatus_Response>()
{
  return collision_management::srv::builder::Init_GetCollisionStatus_Response_in_collision();
}

}  // namespace collision_management

#endif  // COLLISION_MANAGEMENT__SRV__DETAIL__GET_COLLISION_STATUS__BUILDER_HPP_
