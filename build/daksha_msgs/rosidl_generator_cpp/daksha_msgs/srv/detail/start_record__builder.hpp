// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from daksha_msgs:srv/StartRecord.idl
// generated code does not contain a copyright notice

#ifndef DAKSHA_MSGS__SRV__DETAIL__START_RECORD__BUILDER_HPP_
#define DAKSHA_MSGS__SRV__DETAIL__START_RECORD__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "daksha_msgs/srv/detail/start_record__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace daksha_msgs
{

namespace srv
{

namespace builder
{

class Init_StartRecord_Request_max_episodes
{
public:
  explicit Init_StartRecord_Request_max_episodes(::daksha_msgs::srv::StartRecord_Request & msg)
  : msg_(msg)
  {}
  ::daksha_msgs::srv::StartRecord_Request max_episodes(::daksha_msgs::srv::StartRecord_Request::_max_episodes_type arg)
  {
    msg_.max_episodes = std::move(arg);
    return std::move(msg_);
  }

private:
  ::daksha_msgs::srv::StartRecord_Request msg_;
};

class Init_StartRecord_Request_record_hz
{
public:
  explicit Init_StartRecord_Request_record_hz(::daksha_msgs::srv::StartRecord_Request & msg)
  : msg_(msg)
  {}
  Init_StartRecord_Request_max_episodes record_hz(::daksha_msgs::srv::StartRecord_Request::_record_hz_type arg)
  {
    msg_.record_hz = std::move(arg);
    return Init_StartRecord_Request_max_episodes(msg_);
  }

private:
  ::daksha_msgs::srv::StartRecord_Request msg_;
};

class Init_StartRecord_Request_episode_length
{
public:
  explicit Init_StartRecord_Request_episode_length(::daksha_msgs::srv::StartRecord_Request & msg)
  : msg_(msg)
  {}
  Init_StartRecord_Request_record_hz episode_length(::daksha_msgs::srv::StartRecord_Request::_episode_length_type arg)
  {
    msg_.episode_length = std::move(arg);
    return Init_StartRecord_Request_record_hz(msg_);
  }

private:
  ::daksha_msgs::srv::StartRecord_Request msg_;
};

class Init_StartRecord_Request_dataset_name
{
public:
  Init_StartRecord_Request_dataset_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_StartRecord_Request_episode_length dataset_name(::daksha_msgs::srv::StartRecord_Request::_dataset_name_type arg)
  {
    msg_.dataset_name = std::move(arg);
    return Init_StartRecord_Request_episode_length(msg_);
  }

private:
  ::daksha_msgs::srv::StartRecord_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::daksha_msgs::srv::StartRecord_Request>()
{
  return daksha_msgs::srv::builder::Init_StartRecord_Request_dataset_name();
}

}  // namespace daksha_msgs


namespace daksha_msgs
{

namespace srv
{

namespace builder
{

class Init_StartRecord_Response_message
{
public:
  explicit Init_StartRecord_Response_message(::daksha_msgs::srv::StartRecord_Response & msg)
  : msg_(msg)
  {}
  ::daksha_msgs::srv::StartRecord_Response message(::daksha_msgs::srv::StartRecord_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::daksha_msgs::srv::StartRecord_Response msg_;
};

class Init_StartRecord_Response_success
{
public:
  Init_StartRecord_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_StartRecord_Response_message success(::daksha_msgs::srv::StartRecord_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_StartRecord_Response_message(msg_);
  }

private:
  ::daksha_msgs::srv::StartRecord_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::daksha_msgs::srv::StartRecord_Response>()
{
  return daksha_msgs::srv::builder::Init_StartRecord_Response_success();
}

}  // namespace daksha_msgs

#endif  // DAKSHA_MSGS__SRV__DETAIL__START_RECORD__BUILDER_HPP_
