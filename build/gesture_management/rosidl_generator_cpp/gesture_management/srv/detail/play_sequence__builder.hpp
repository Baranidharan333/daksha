// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from gesture_management:srv/PlaySequence.idl
// generated code does not contain a copyright notice

#ifndef GESTURE_MANAGEMENT__SRV__DETAIL__PLAY_SEQUENCE__BUILDER_HPP_
#define GESTURE_MANAGEMENT__SRV__DETAIL__PLAY_SEQUENCE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "gesture_management/srv/detail/play_sequence__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace gesture_management
{

namespace srv
{

namespace builder
{

class Init_PlaySequence_Request_interval_s
{
public:
  explicit Init_PlaySequence_Request_interval_s(::gesture_management::srv::PlaySequence_Request & msg)
  : msg_(msg)
  {}
  ::gesture_management::srv::PlaySequence_Request interval_s(::gesture_management::srv::PlaySequence_Request::_interval_s_type arg)
  {
    msg_.interval_s = std::move(arg);
    return std::move(msg_);
  }

private:
  ::gesture_management::srv::PlaySequence_Request msg_;
};

class Init_PlaySequence_Request_repeat_count
{
public:
  explicit Init_PlaySequence_Request_repeat_count(::gesture_management::srv::PlaySequence_Request & msg)
  : msg_(msg)
  {}
  Init_PlaySequence_Request_interval_s repeat_count(::gesture_management::srv::PlaySequence_Request::_repeat_count_type arg)
  {
    msg_.repeat_count = std::move(arg);
    return Init_PlaySequence_Request_interval_s(msg_);
  }

private:
  ::gesture_management::srv::PlaySequence_Request msg_;
};

class Init_PlaySequence_Request_repeat_mode
{
public:
  explicit Init_PlaySequence_Request_repeat_mode(::gesture_management::srv::PlaySequence_Request & msg)
  : msg_(msg)
  {}
  Init_PlaySequence_Request_repeat_count repeat_mode(::gesture_management::srv::PlaySequence_Request::_repeat_mode_type arg)
  {
    msg_.repeat_mode = std::move(arg);
    return Init_PlaySequence_Request_repeat_count(msg_);
  }

private:
  ::gesture_management::srv::PlaySequence_Request msg_;
};

class Init_PlaySequence_Request_replay_speed
{
public:
  explicit Init_PlaySequence_Request_replay_speed(::gesture_management::srv::PlaySequence_Request & msg)
  : msg_(msg)
  {}
  Init_PlaySequence_Request_repeat_mode replay_speed(::gesture_management::srv::PlaySequence_Request::_replay_speed_type arg)
  {
    msg_.replay_speed = std::move(arg);
    return Init_PlaySequence_Request_repeat_mode(msg_);
  }

private:
  ::gesture_management::srv::PlaySequence_Request msg_;
};

class Init_PlaySequence_Request_output_topic
{
public:
  explicit Init_PlaySequence_Request_output_topic(::gesture_management::srv::PlaySequence_Request & msg)
  : msg_(msg)
  {}
  Init_PlaySequence_Request_replay_speed output_topic(::gesture_management::srv::PlaySequence_Request::_output_topic_type arg)
  {
    msg_.output_topic = std::move(arg);
    return Init_PlaySequence_Request_replay_speed(msg_);
  }

private:
  ::gesture_management::srv::PlaySequence_Request msg_;
};

class Init_PlaySequence_Request_recording_names
{
public:
  explicit Init_PlaySequence_Request_recording_names(::gesture_management::srv::PlaySequence_Request & msg)
  : msg_(msg)
  {}
  Init_PlaySequence_Request_output_topic recording_names(::gesture_management::srv::PlaySequence_Request::_recording_names_type arg)
  {
    msg_.recording_names = std::move(arg);
    return Init_PlaySequence_Request_output_topic(msg_);
  }

private:
  ::gesture_management::srv::PlaySequence_Request msg_;
};

class Init_PlaySequence_Request_sequence_name
{
public:
  Init_PlaySequence_Request_sequence_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_PlaySequence_Request_recording_names sequence_name(::gesture_management::srv::PlaySequence_Request::_sequence_name_type arg)
  {
    msg_.sequence_name = std::move(arg);
    return Init_PlaySequence_Request_recording_names(msg_);
  }

private:
  ::gesture_management::srv::PlaySequence_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::gesture_management::srv::PlaySequence_Request>()
{
  return gesture_management::srv::builder::Init_PlaySequence_Request_sequence_name();
}

}  // namespace gesture_management


namespace gesture_management
{

namespace srv
{

namespace builder
{

class Init_PlaySequence_Response_message
{
public:
  explicit Init_PlaySequence_Response_message(::gesture_management::srv::PlaySequence_Response & msg)
  : msg_(msg)
  {}
  ::gesture_management::srv::PlaySequence_Response message(::gesture_management::srv::PlaySequence_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::gesture_management::srv::PlaySequence_Response msg_;
};

class Init_PlaySequence_Response_success
{
public:
  Init_PlaySequence_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_PlaySequence_Response_message success(::gesture_management::srv::PlaySequence_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_PlaySequence_Response_message(msg_);
  }

private:
  ::gesture_management::srv::PlaySequence_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::gesture_management::srv::PlaySequence_Response>()
{
  return gesture_management::srv::builder::Init_PlaySequence_Response_success();
}

}  // namespace gesture_management

#endif  // GESTURE_MANAGEMENT__SRV__DETAIL__PLAY_SEQUENCE__BUILDER_HPP_
