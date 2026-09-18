// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from gesture_management:srv/PlayRecording.idl
// generated code does not contain a copyright notice

#ifndef GESTURE_MANAGEMENT__SRV__DETAIL__PLAY_RECORDING__BUILDER_HPP_
#define GESTURE_MANAGEMENT__SRV__DETAIL__PLAY_RECORDING__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "gesture_management/srv/detail/play_recording__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace gesture_management
{

namespace srv
{

namespace builder
{

class Init_PlayRecording_Request_interval_s
{
public:
  explicit Init_PlayRecording_Request_interval_s(::gesture_management::srv::PlayRecording_Request & msg)
  : msg_(msg)
  {}
  ::gesture_management::srv::PlayRecording_Request interval_s(::gesture_management::srv::PlayRecording_Request::_interval_s_type arg)
  {
    msg_.interval_s = std::move(arg);
    return std::move(msg_);
  }

private:
  ::gesture_management::srv::PlayRecording_Request msg_;
};

class Init_PlayRecording_Request_repeat_count
{
public:
  explicit Init_PlayRecording_Request_repeat_count(::gesture_management::srv::PlayRecording_Request & msg)
  : msg_(msg)
  {}
  Init_PlayRecording_Request_interval_s repeat_count(::gesture_management::srv::PlayRecording_Request::_repeat_count_type arg)
  {
    msg_.repeat_count = std::move(arg);
    return Init_PlayRecording_Request_interval_s(msg_);
  }

private:
  ::gesture_management::srv::PlayRecording_Request msg_;
};

class Init_PlayRecording_Request_repeat_mode
{
public:
  explicit Init_PlayRecording_Request_repeat_mode(::gesture_management::srv::PlayRecording_Request & msg)
  : msg_(msg)
  {}
  Init_PlayRecording_Request_repeat_count repeat_mode(::gesture_management::srv::PlayRecording_Request::_repeat_mode_type arg)
  {
    msg_.repeat_mode = std::move(arg);
    return Init_PlayRecording_Request_repeat_count(msg_);
  }

private:
  ::gesture_management::srv::PlayRecording_Request msg_;
};

class Init_PlayRecording_Request_replay_speed
{
public:
  explicit Init_PlayRecording_Request_replay_speed(::gesture_management::srv::PlayRecording_Request & msg)
  : msg_(msg)
  {}
  Init_PlayRecording_Request_repeat_mode replay_speed(::gesture_management::srv::PlayRecording_Request::_replay_speed_type arg)
  {
    msg_.replay_speed = std::move(arg);
    return Init_PlayRecording_Request_repeat_mode(msg_);
  }

private:
  ::gesture_management::srv::PlayRecording_Request msg_;
};

class Init_PlayRecording_Request_output_topic
{
public:
  explicit Init_PlayRecording_Request_output_topic(::gesture_management::srv::PlayRecording_Request & msg)
  : msg_(msg)
  {}
  Init_PlayRecording_Request_replay_speed output_topic(::gesture_management::srv::PlayRecording_Request::_output_topic_type arg)
  {
    msg_.output_topic = std::move(arg);
    return Init_PlayRecording_Request_replay_speed(msg_);
  }

private:
  ::gesture_management::srv::PlayRecording_Request msg_;
};

class Init_PlayRecording_Request_recording_name
{
public:
  Init_PlayRecording_Request_recording_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_PlayRecording_Request_output_topic recording_name(::gesture_management::srv::PlayRecording_Request::_recording_name_type arg)
  {
    msg_.recording_name = std::move(arg);
    return Init_PlayRecording_Request_output_topic(msg_);
  }

private:
  ::gesture_management::srv::PlayRecording_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::gesture_management::srv::PlayRecording_Request>()
{
  return gesture_management::srv::builder::Init_PlayRecording_Request_recording_name();
}

}  // namespace gesture_management


namespace gesture_management
{

namespace srv
{

namespace builder
{

class Init_PlayRecording_Response_message
{
public:
  explicit Init_PlayRecording_Response_message(::gesture_management::srv::PlayRecording_Response & msg)
  : msg_(msg)
  {}
  ::gesture_management::srv::PlayRecording_Response message(::gesture_management::srv::PlayRecording_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::gesture_management::srv::PlayRecording_Response msg_;
};

class Init_PlayRecording_Response_success
{
public:
  Init_PlayRecording_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_PlayRecording_Response_message success(::gesture_management::srv::PlayRecording_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_PlayRecording_Response_message(msg_);
  }

private:
  ::gesture_management::srv::PlayRecording_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::gesture_management::srv::PlayRecording_Response>()
{
  return gesture_management::srv::builder::Init_PlayRecording_Response_success();
}

}  // namespace gesture_management

#endif  // GESTURE_MANAGEMENT__SRV__DETAIL__PLAY_RECORDING__BUILDER_HPP_
