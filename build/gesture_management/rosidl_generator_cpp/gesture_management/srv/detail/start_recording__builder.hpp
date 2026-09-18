// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from gesture_management:srv/StartRecording.idl
// generated code does not contain a copyright notice

#ifndef GESTURE_MANAGEMENT__SRV__DETAIL__START_RECORDING__BUILDER_HPP_
#define GESTURE_MANAGEMENT__SRV__DETAIL__START_RECORDING__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "gesture_management/srv/detail/start_recording__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace gesture_management
{

namespace srv
{

namespace builder
{

class Init_StartRecording_Request_action
{
public:
  explicit Init_StartRecording_Request_action(::gesture_management::srv::StartRecording_Request & msg)
  : msg_(msg)
  {}
  ::gesture_management::srv::StartRecording_Request action(::gesture_management::srv::StartRecording_Request::_action_type arg)
  {
    msg_.action = std::move(arg);
    return std::move(msg_);
  }

private:
  ::gesture_management::srv::StartRecording_Request msg_;
};

class Init_StartRecording_Request_recording_name
{
public:
  explicit Init_StartRecording_Request_recording_name(::gesture_management::srv::StartRecording_Request & msg)
  : msg_(msg)
  {}
  Init_StartRecording_Request_action recording_name(::gesture_management::srv::StartRecording_Request::_recording_name_type arg)
  {
    msg_.recording_name = std::move(arg);
    return Init_StartRecording_Request_action(msg_);
  }

private:
  ::gesture_management::srv::StartRecording_Request msg_;
};

class Init_StartRecording_Request_topic_name
{
public:
  Init_StartRecording_Request_topic_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_StartRecording_Request_recording_name topic_name(::gesture_management::srv::StartRecording_Request::_topic_name_type arg)
  {
    msg_.topic_name = std::move(arg);
    return Init_StartRecording_Request_recording_name(msg_);
  }

private:
  ::gesture_management::srv::StartRecording_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::gesture_management::srv::StartRecording_Request>()
{
  return gesture_management::srv::builder::Init_StartRecording_Request_topic_name();
}

}  // namespace gesture_management


namespace gesture_management
{

namespace srv
{

namespace builder
{

class Init_StartRecording_Response_message
{
public:
  explicit Init_StartRecording_Response_message(::gesture_management::srv::StartRecording_Response & msg)
  : msg_(msg)
  {}
  ::gesture_management::srv::StartRecording_Response message(::gesture_management::srv::StartRecording_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::gesture_management::srv::StartRecording_Response msg_;
};

class Init_StartRecording_Response_success
{
public:
  Init_StartRecording_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_StartRecording_Response_message success(::gesture_management::srv::StartRecording_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_StartRecording_Response_message(msg_);
  }

private:
  ::gesture_management::srv::StartRecording_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::gesture_management::srv::StartRecording_Response>()
{
  return gesture_management::srv::builder::Init_StartRecording_Response_success();
}

}  // namespace gesture_management

#endif  // GESTURE_MANAGEMENT__SRV__DETAIL__START_RECORDING__BUILDER_HPP_
