// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from gesture_management:srv/ReplayRecording.idl
// generated code does not contain a copyright notice

#ifndef GESTURE_MANAGEMENT__SRV__DETAIL__REPLAY_RECORDING__TRAITS_HPP_
#define GESTURE_MANAGEMENT__SRV__DETAIL__REPLAY_RECORDING__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "gesture_management/srv/detail/replay_recording__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace gesture_management
{

namespace srv
{

inline void to_flow_style_yaml(
  const ReplayRecording_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: recording_name
  {
    out << "recording_name: ";
    rosidl_generator_traits::value_to_yaml(msg.recording_name, out);
    out << ", ";
  }

  // member: output_topic
  {
    out << "output_topic: ";
    rosidl_generator_traits::value_to_yaml(msg.output_topic, out);
    out << ", ";
  }

  // member: replay_speed
  {
    out << "replay_speed: ";
    rosidl_generator_traits::value_to_yaml(msg.replay_speed, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const ReplayRecording_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: recording_name
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "recording_name: ";
    rosidl_generator_traits::value_to_yaml(msg.recording_name, out);
    out << "\n";
  }

  // member: output_topic
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "output_topic: ";
    rosidl_generator_traits::value_to_yaml(msg.output_topic, out);
    out << "\n";
  }

  // member: replay_speed
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "replay_speed: ";
    rosidl_generator_traits::value_to_yaml(msg.replay_speed, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ReplayRecording_Request & msg, bool use_flow_style = false)
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

}  // namespace gesture_management

namespace rosidl_generator_traits
{

[[deprecated("use gesture_management::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const gesture_management::srv::ReplayRecording_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  gesture_management::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use gesture_management::srv::to_yaml() instead")]]
inline std::string to_yaml(const gesture_management::srv::ReplayRecording_Request & msg)
{
  return gesture_management::srv::to_yaml(msg);
}

template<>
inline const char * data_type<gesture_management::srv::ReplayRecording_Request>()
{
  return "gesture_management::srv::ReplayRecording_Request";
}

template<>
inline const char * name<gesture_management::srv::ReplayRecording_Request>()
{
  return "gesture_management/srv/ReplayRecording_Request";
}

template<>
struct has_fixed_size<gesture_management::srv::ReplayRecording_Request>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<gesture_management::srv::ReplayRecording_Request>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<gesture_management::srv::ReplayRecording_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace gesture_management
{

namespace srv
{

inline void to_flow_style_yaml(
  const ReplayRecording_Response & msg,
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
  const ReplayRecording_Response & msg,
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

inline std::string to_yaml(const ReplayRecording_Response & msg, bool use_flow_style = false)
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

}  // namespace gesture_management

namespace rosidl_generator_traits
{

[[deprecated("use gesture_management::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const gesture_management::srv::ReplayRecording_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  gesture_management::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use gesture_management::srv::to_yaml() instead")]]
inline std::string to_yaml(const gesture_management::srv::ReplayRecording_Response & msg)
{
  return gesture_management::srv::to_yaml(msg);
}

template<>
inline const char * data_type<gesture_management::srv::ReplayRecording_Response>()
{
  return "gesture_management::srv::ReplayRecording_Response";
}

template<>
inline const char * name<gesture_management::srv::ReplayRecording_Response>()
{
  return "gesture_management/srv/ReplayRecording_Response";
}

template<>
struct has_fixed_size<gesture_management::srv::ReplayRecording_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<gesture_management::srv::ReplayRecording_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<gesture_management::srv::ReplayRecording_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<gesture_management::srv::ReplayRecording>()
{
  return "gesture_management::srv::ReplayRecording";
}

template<>
inline const char * name<gesture_management::srv::ReplayRecording>()
{
  return "gesture_management/srv/ReplayRecording";
}

template<>
struct has_fixed_size<gesture_management::srv::ReplayRecording>
  : std::integral_constant<
    bool,
    has_fixed_size<gesture_management::srv::ReplayRecording_Request>::value &&
    has_fixed_size<gesture_management::srv::ReplayRecording_Response>::value
  >
{
};

template<>
struct has_bounded_size<gesture_management::srv::ReplayRecording>
  : std::integral_constant<
    bool,
    has_bounded_size<gesture_management::srv::ReplayRecording_Request>::value &&
    has_bounded_size<gesture_management::srv::ReplayRecording_Response>::value
  >
{
};

template<>
struct is_service<gesture_management::srv::ReplayRecording>
  : std::true_type
{
};

template<>
struct is_service_request<gesture_management::srv::ReplayRecording_Request>
  : std::true_type
{
};

template<>
struct is_service_response<gesture_management::srv::ReplayRecording_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // GESTURE_MANAGEMENT__SRV__DETAIL__REPLAY_RECORDING__TRAITS_HPP_
