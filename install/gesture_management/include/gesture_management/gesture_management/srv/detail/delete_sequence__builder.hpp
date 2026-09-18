// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from gesture_management:srv/DeleteSequence.idl
// generated code does not contain a copyright notice

#ifndef GESTURE_MANAGEMENT__SRV__DETAIL__DELETE_SEQUENCE__BUILDER_HPP_
#define GESTURE_MANAGEMENT__SRV__DETAIL__DELETE_SEQUENCE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "gesture_management/srv/detail/delete_sequence__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace gesture_management
{

namespace srv
{

namespace builder
{

class Init_DeleteSequence_Request_name
{
public:
  Init_DeleteSequence_Request_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::gesture_management::srv::DeleteSequence_Request name(::gesture_management::srv::DeleteSequence_Request::_name_type arg)
  {
    msg_.name = std::move(arg);
    return std::move(msg_);
  }

private:
  ::gesture_management::srv::DeleteSequence_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::gesture_management::srv::DeleteSequence_Request>()
{
  return gesture_management::srv::builder::Init_DeleteSequence_Request_name();
}

}  // namespace gesture_management


namespace gesture_management
{

namespace srv
{

namespace builder
{

class Init_DeleteSequence_Response_message
{
public:
  explicit Init_DeleteSequence_Response_message(::gesture_management::srv::DeleteSequence_Response & msg)
  : msg_(msg)
  {}
  ::gesture_management::srv::DeleteSequence_Response message(::gesture_management::srv::DeleteSequence_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::gesture_management::srv::DeleteSequence_Response msg_;
};

class Init_DeleteSequence_Response_success
{
public:
  Init_DeleteSequence_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DeleteSequence_Response_message success(::gesture_management::srv::DeleteSequence_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_DeleteSequence_Response_message(msg_);
  }

private:
  ::gesture_management::srv::DeleteSequence_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::gesture_management::srv::DeleteSequence_Response>()
{
  return gesture_management::srv::builder::Init_DeleteSequence_Response_success();
}

}  // namespace gesture_management

#endif  // GESTURE_MANAGEMENT__SRV__DETAIL__DELETE_SEQUENCE__BUILDER_HPP_
