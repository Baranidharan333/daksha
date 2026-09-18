// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from gesture_management:srv/ListSequences.idl
// generated code does not contain a copyright notice

#ifndef GESTURE_MANAGEMENT__SRV__DETAIL__LIST_SEQUENCES__BUILDER_HPP_
#define GESTURE_MANAGEMENT__SRV__DETAIL__LIST_SEQUENCES__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "gesture_management/srv/detail/list_sequences__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace gesture_management
{

namespace srv
{


}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::gesture_management::srv::ListSequences_Request>()
{
  return ::gesture_management::srv::ListSequences_Request(rosidl_runtime_cpp::MessageInitialization::ZERO);
}

}  // namespace gesture_management


namespace gesture_management
{

namespace srv
{

namespace builder
{

class Init_ListSequences_Response_sequences_json
{
public:
  explicit Init_ListSequences_Response_sequences_json(::gesture_management::srv::ListSequences_Response & msg)
  : msg_(msg)
  {}
  ::gesture_management::srv::ListSequences_Response sequences_json(::gesture_management::srv::ListSequences_Response::_sequences_json_type arg)
  {
    msg_.sequences_json = std::move(arg);
    return std::move(msg_);
  }

private:
  ::gesture_management::srv::ListSequences_Response msg_;
};

class Init_ListSequences_Response_success
{
public:
  Init_ListSequences_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ListSequences_Response_sequences_json success(::gesture_management::srv::ListSequences_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_ListSequences_Response_sequences_json(msg_);
  }

private:
  ::gesture_management::srv::ListSequences_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::gesture_management::srv::ListSequences_Response>()
{
  return gesture_management::srv::builder::Init_ListSequences_Response_success();
}

}  // namespace gesture_management

#endif  // GESTURE_MANAGEMENT__SRV__DETAIL__LIST_SEQUENCES__BUILDER_HPP_
