// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from gesture_management:srv/GetReplayStatus.idl
// generated code does not contain a copyright notice

#ifndef GESTURE_MANAGEMENT__SRV__DETAIL__GET_REPLAY_STATUS__TRAITS_HPP_
#define GESTURE_MANAGEMENT__SRV__DETAIL__GET_REPLAY_STATUS__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "gesture_management/srv/detail/get_replay_status__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace gesture_management
{

namespace srv
{

inline void to_flow_style_yaml(
  const GetReplayStatus_Request & msg,
  std::ostream & out)
{
  (void)msg;
  out << "null";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const GetReplayStatus_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  (void)msg;
  (void)indentation;
  out << "null\n";
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const GetReplayStatus_Request & msg, bool use_flow_style = false)
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
  const gesture_management::srv::GetReplayStatus_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  gesture_management::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use gesture_management::srv::to_yaml() instead")]]
inline std::string to_yaml(const gesture_management::srv::GetReplayStatus_Request & msg)
{
  return gesture_management::srv::to_yaml(msg);
}

template<>
inline const char * data_type<gesture_management::srv::GetReplayStatus_Request>()
{
  return "gesture_management::srv::GetReplayStatus_Request";
}

template<>
inline const char * name<gesture_management::srv::GetReplayStatus_Request>()
{
  return "gesture_management/srv/GetReplayStatus_Request";
}

template<>
struct has_fixed_size<gesture_management::srv::GetReplayStatus_Request>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<gesture_management::srv::GetReplayStatus_Request>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<gesture_management::srv::GetReplayStatus_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace gesture_management
{

namespace srv
{

inline void to_flow_style_yaml(
  const GetReplayStatus_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: success
  {
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << ", ";
  }

  // member: status_json
  {
    out << "status_json: ";
    rosidl_generator_traits::value_to_yaml(msg.status_json, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const GetReplayStatus_Response & msg,
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

  // member: status_json
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "status_json: ";
    rosidl_generator_traits::value_to_yaml(msg.status_json, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const GetReplayStatus_Response & msg, bool use_flow_style = false)
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
  const gesture_management::srv::GetReplayStatus_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  gesture_management::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use gesture_management::srv::to_yaml() instead")]]
inline std::string to_yaml(const gesture_management::srv::GetReplayStatus_Response & msg)
{
  return gesture_management::srv::to_yaml(msg);
}

template<>
inline const char * data_type<gesture_management::srv::GetReplayStatus_Response>()
{
  return "gesture_management::srv::GetReplayStatus_Response";
}

template<>
inline const char * name<gesture_management::srv::GetReplayStatus_Response>()
{
  return "gesture_management/srv/GetReplayStatus_Response";
}

template<>
struct has_fixed_size<gesture_management::srv::GetReplayStatus_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<gesture_management::srv::GetReplayStatus_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<gesture_management::srv::GetReplayStatus_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<gesture_management::srv::GetReplayStatus>()
{
  return "gesture_management::srv::GetReplayStatus";
}

template<>
inline const char * name<gesture_management::srv::GetReplayStatus>()
{
  return "gesture_management/srv/GetReplayStatus";
}

template<>
struct has_fixed_size<gesture_management::srv::GetReplayStatus>
  : std::integral_constant<
    bool,
    has_fixed_size<gesture_management::srv::GetReplayStatus_Request>::value &&
    has_fixed_size<gesture_management::srv::GetReplayStatus_Response>::value
  >
{
};

template<>
struct has_bounded_size<gesture_management::srv::GetReplayStatus>
  : std::integral_constant<
    bool,
    has_bounded_size<gesture_management::srv::GetReplayStatus_Request>::value &&
    has_bounded_size<gesture_management::srv::GetReplayStatus_Response>::value
  >
{
};

template<>
struct is_service<gesture_management::srv::GetReplayStatus>
  : std::true_type
{
};

template<>
struct is_service_request<gesture_management::srv::GetReplayStatus_Request>
  : std::true_type
{
};

template<>
struct is_service_response<gesture_management::srv::GetReplayStatus_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // GESTURE_MANAGEMENT__SRV__DETAIL__GET_REPLAY_STATUS__TRAITS_HPP_
