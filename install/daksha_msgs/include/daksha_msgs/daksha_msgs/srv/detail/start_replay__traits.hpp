// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from daksha_msgs:srv/StartReplay.idl
// generated code does not contain a copyright notice

#ifndef DAKSHA_MSGS__SRV__DETAIL__START_REPLAY__TRAITS_HPP_
#define DAKSHA_MSGS__SRV__DETAIL__START_REPLAY__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "daksha_msgs/srv/detail/start_replay__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace daksha_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const StartReplay_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: dataset_name
  {
    out << "dataset_name: ";
    rosidl_generator_traits::value_to_yaml(msg.dataset_name, out);
    out << ", ";
  }

  // member: episode_index
  {
    out << "episode_index: ";
    rosidl_generator_traits::value_to_yaml(msg.episode_index, out);
    out << ", ";
  }

  // member: speed
  {
    out << "speed: ";
    rosidl_generator_traits::value_to_yaml(msg.speed, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const StartReplay_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: dataset_name
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "dataset_name: ";
    rosidl_generator_traits::value_to_yaml(msg.dataset_name, out);
    out << "\n";
  }

  // member: episode_index
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "episode_index: ";
    rosidl_generator_traits::value_to_yaml(msg.episode_index, out);
    out << "\n";
  }

  // member: speed
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "speed: ";
    rosidl_generator_traits::value_to_yaml(msg.speed, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const StartReplay_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace daksha_msgs

namespace rosidl_generator_traits
{

[[deprecated("use daksha_msgs::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const daksha_msgs::srv::StartReplay_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  daksha_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use daksha_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const daksha_msgs::srv::StartReplay_Request & msg)
{
  return daksha_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<daksha_msgs::srv::StartReplay_Request>()
{
  return "daksha_msgs::srv::StartReplay_Request";
}

template<>
inline const char * name<daksha_msgs::srv::StartReplay_Request>()
{
  return "daksha_msgs/srv/StartReplay_Request";
}

template<>
struct has_fixed_size<daksha_msgs::srv::StartReplay_Request>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<daksha_msgs::srv::StartReplay_Request>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<daksha_msgs::srv::StartReplay_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace daksha_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const StartReplay_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: success
  {
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << ", ";
  }

  // member: message
  {
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const StartReplay_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: success
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << "\n";
  }

  // member: message
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const StartReplay_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace daksha_msgs

namespace rosidl_generator_traits
{

[[deprecated("use daksha_msgs::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const daksha_msgs::srv::StartReplay_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  daksha_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use daksha_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const daksha_msgs::srv::StartReplay_Response & msg)
{
  return daksha_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<daksha_msgs::srv::StartReplay_Response>()
{
  return "daksha_msgs::srv::StartReplay_Response";
}

template<>
inline const char * name<daksha_msgs::srv::StartReplay_Response>()
{
  return "daksha_msgs/srv/StartReplay_Response";
}

template<>
struct has_fixed_size<daksha_msgs::srv::StartReplay_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<daksha_msgs::srv::StartReplay_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<daksha_msgs::srv::StartReplay_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<daksha_msgs::srv::StartReplay>()
{
  return "daksha_msgs::srv::StartReplay";
}

template<>
inline const char * name<daksha_msgs::srv::StartReplay>()
{
  return "daksha_msgs/srv/StartReplay";
}

template<>
struct has_fixed_size<daksha_msgs::srv::StartReplay>
  : std::integral_constant<
    bool,
    has_fixed_size<daksha_msgs::srv::StartReplay_Request>::value &&
    has_fixed_size<daksha_msgs::srv::StartReplay_Response>::value
  >
{
};

template<>
struct has_bounded_size<daksha_msgs::srv::StartReplay>
  : std::integral_constant<
    bool,
    has_bounded_size<daksha_msgs::srv::StartReplay_Request>::value &&
    has_bounded_size<daksha_msgs::srv::StartReplay_Response>::value
  >
{
};

template<>
struct is_service<daksha_msgs::srv::StartReplay>
  : std::true_type
{
};

template<>
struct is_service_request<daksha_msgs::srv::StartReplay_Request>
  : std::true_type
{
};

template<>
struct is_service_response<daksha_msgs::srv::StartReplay_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // DAKSHA_MSGS__SRV__DETAIL__START_REPLAY__TRAITS_HPP_
