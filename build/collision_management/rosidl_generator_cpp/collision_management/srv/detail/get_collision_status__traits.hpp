// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from collision_management:srv/GetCollisionStatus.idl
// generated code does not contain a copyright notice

#ifndef COLLISION_MANAGEMENT__SRV__DETAIL__GET_COLLISION_STATUS__TRAITS_HPP_
#define COLLISION_MANAGEMENT__SRV__DETAIL__GET_COLLISION_STATUS__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "collision_management/srv/detail/get_collision_status__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace collision_management
{

namespace srv
{

inline void to_flow_style_yaml(
  const GetCollisionStatus_Request & msg,
  std::ostream & out)
{
  (void)msg;
  out << "null";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const GetCollisionStatus_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  (void)msg;
  (void)indentation;
  out << "null\n";
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const GetCollisionStatus_Request & msg, bool use_flow_style = false)
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

}  // namespace collision_management

namespace rosidl_generator_traits
{

[[deprecated("use collision_management::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const collision_management::srv::GetCollisionStatus_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  collision_management::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use collision_management::srv::to_yaml() instead")]]
inline std::string to_yaml(const collision_management::srv::GetCollisionStatus_Request & msg)
{
  return collision_management::srv::to_yaml(msg);
}

template<>
inline const char * data_type<collision_management::srv::GetCollisionStatus_Request>()
{
  return "collision_management::srv::GetCollisionStatus_Request";
}

template<>
inline const char * name<collision_management::srv::GetCollisionStatus_Request>()
{
  return "collision_management/srv/GetCollisionStatus_Request";
}

template<>
struct has_fixed_size<collision_management::srv::GetCollisionStatus_Request>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<collision_management::srv::GetCollisionStatus_Request>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<collision_management::srv::GetCollisionStatus_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'status'
#include "sensor_msgs/msg/detail/joint_state__traits.hpp"

namespace collision_management
{

namespace srv
{

inline void to_flow_style_yaml(
  const GetCollisionStatus_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: in_collision
  {
    out << "in_collision: ";
    rosidl_generator_traits::value_to_yaml(msg.in_collision, out);
    out << ", ";
  }

  // member: status
  {
    out << "status: ";
    to_flow_style_yaml(msg.status, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const GetCollisionStatus_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: in_collision
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "in_collision: ";
    rosidl_generator_traits::value_to_yaml(msg.in_collision, out);
    out << "\n";
  }

  // member: status
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "status:\n";
    to_block_style_yaml(msg.status, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const GetCollisionStatus_Response & msg, bool use_flow_style = false)
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

}  // namespace collision_management

namespace rosidl_generator_traits
{

[[deprecated("use collision_management::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const collision_management::srv::GetCollisionStatus_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  collision_management::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use collision_management::srv::to_yaml() instead")]]
inline std::string to_yaml(const collision_management::srv::GetCollisionStatus_Response & msg)
{
  return collision_management::srv::to_yaml(msg);
}

template<>
inline const char * data_type<collision_management::srv::GetCollisionStatus_Response>()
{
  return "collision_management::srv::GetCollisionStatus_Response";
}

template<>
inline const char * name<collision_management::srv::GetCollisionStatus_Response>()
{
  return "collision_management/srv/GetCollisionStatus_Response";
}

template<>
struct has_fixed_size<collision_management::srv::GetCollisionStatus_Response>
  : std::integral_constant<bool, has_fixed_size<sensor_msgs::msg::JointState>::value> {};

template<>
struct has_bounded_size<collision_management::srv::GetCollisionStatus_Response>
  : std::integral_constant<bool, has_bounded_size<sensor_msgs::msg::JointState>::value> {};

template<>
struct is_message<collision_management::srv::GetCollisionStatus_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<collision_management::srv::GetCollisionStatus>()
{
  return "collision_management::srv::GetCollisionStatus";
}

template<>
inline const char * name<collision_management::srv::GetCollisionStatus>()
{
  return "collision_management/srv/GetCollisionStatus";
}

template<>
struct has_fixed_size<collision_management::srv::GetCollisionStatus>
  : std::integral_constant<
    bool,
    has_fixed_size<collision_management::srv::GetCollisionStatus_Request>::value &&
    has_fixed_size<collision_management::srv::GetCollisionStatus_Response>::value
  >
{
};

template<>
struct has_bounded_size<collision_management::srv::GetCollisionStatus>
  : std::integral_constant<
    bool,
    has_bounded_size<collision_management::srv::GetCollisionStatus_Request>::value &&
    has_bounded_size<collision_management::srv::GetCollisionStatus_Response>::value
  >
{
};

template<>
struct is_service<collision_management::srv::GetCollisionStatus>
  : std::true_type
{
};

template<>
struct is_service_request<collision_management::srv::GetCollisionStatus_Request>
  : std::true_type
{
};

template<>
struct is_service_response<collision_management::srv::GetCollisionStatus_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // COLLISION_MANAGEMENT__SRV__DETAIL__GET_COLLISION_STATUS__TRAITS_HPP_
