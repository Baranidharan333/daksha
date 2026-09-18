// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from daksha_msgs:srv/StartReplay.idl
// generated code does not contain a copyright notice

#ifndef DAKSHA_MSGS__SRV__DETAIL__START_REPLAY__BUILDER_HPP_
#define DAKSHA_MSGS__SRV__DETAIL__START_REPLAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "daksha_msgs/srv/detail/start_replay__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace daksha_msgs
{

namespace srv
{

namespace builder
{

class Init_StartReplay_Request_speed
{
public:
  explicit Init_StartReplay_Request_speed(::daksha_msgs::srv::StartReplay_Request & msg)
  : msg_(msg)
  {}
  ::daksha_msgs::srv::StartReplay_Request speed(::daksha_msgs::srv::StartReplay_Request::_speed_type arg)
  {
    msg_.speed = std::move(arg);
    return std::move(msg_);
  }

private:
  ::daksha_msgs::srv::StartReplay_Request msg_;
};

class Init_StartReplay_Request_episode_index
{
public:
  explicit Init_StartReplay_Request_episode_index(::daksha_msgs::srv::StartReplay_Request & msg)
  : msg_(msg)
  {}
  Init_StartReplay_Request_speed episode_index(::daksha_msgs::srv::StartReplay_Request::_episode_index_type arg)
  {
    msg_.episode_index = std::move(arg);
    return Init_StartReplay_Request_speed(msg_);
  }

private:
  ::daksha_msgs::srv::StartReplay_Request msg_;
};

class Init_StartReplay_Request_dataset_name
{
public:
  Init_StartReplay_Request_dataset_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_StartReplay_Request_episode_index dataset_name(::daksha_msgs::srv::StartReplay_Request::_dataset_name_type arg)
  {
    msg_.dataset_name = std::move(arg);
    return Init_StartReplay_Request_episode_index(msg_);
  }

private:
  ::daksha_msgs::srv::StartReplay_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::daksha_msgs::srv::StartReplay_Request>()
{
  return daksha_msgs::srv::builder::Init_StartReplay_Request_dataset_name();
}

}  // namespace daksha_msgs


namespace daksha_msgs
{

namespace srv
{

namespace builder
{

class Init_StartReplay_Response_message
{
public:
  explicit Init_StartReplay_Response_message(::daksha_msgs::srv::StartReplay_Response & msg)
  : msg_(msg)
  {}
  ::daksha_msgs::srv::StartReplay_Response message(::daksha_msgs::srv::StartReplay_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::daksha_msgs::srv::StartReplay_Response msg_;
};

class Init_StartReplay_Response_success
{
public:
  Init_StartReplay_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_StartReplay_Response_message success(::daksha_msgs::srv::StartReplay_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_StartReplay_Response_message(msg_);
  }

private:
  ::daksha_msgs::srv::StartReplay_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::daksha_msgs::srv::StartReplay_Response>()
{
  return daksha_msgs::srv::builder::Init_StartReplay_Response_success();
}

}  // namespace daksha_msgs

#endif  // DAKSHA_MSGS__SRV__DETAIL__START_REPLAY__BUILDER_HPP_
