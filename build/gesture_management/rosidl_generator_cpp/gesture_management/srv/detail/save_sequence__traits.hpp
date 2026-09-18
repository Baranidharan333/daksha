// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from gesture_management:srv/SaveSequence.idl
// generated code does not contain a copyright notice

#ifndef GESTURE_MANAGEMENT__SRV__DETAIL__SAVE_SEQUENCE__TRAITS_HPP_
#define GESTURE_MANAGEMENT__SRV__DETAIL__SAVE_SEQUENCE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "gesture_management/srv/detail/save_sequence__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace gesture_management
{

namespace srv
{

inline void to_flow_style_yaml(
  const SaveSequence_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: name
  {
    out << "name: ";
    rosidl_generator_traits::value_to_yaml(msg.name, out);
    out << ", ";
  }

  // member: recording_names
  {
    if (msg.recording_names.size() == 0) {
      out << "recording_names: []";
    } else {
      out << "recording_names: [";
      size_t pending_items = msg.recording_names.size();
      for (auto item : msg.recording_names) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const SaveSequence_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: name
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "name: ";
    rosidl_generator_traits::value_to_yaml(msg.name, out);
    out << "\n";
  }

  // member: recording_names
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.recording_names.size() == 0) {
      out << "recording_names: []\n";
    } else {
      out << "recording_names:\n";
      for (auto item : msg.recording_names) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const SaveSequence_Request & msg, bool use_flow_style = false)
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
  const gesture_management::srv::SaveSequence_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  gesture_management::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use gesture_management::srv::to_yaml() instead")]]
inline std::string to_yaml(const gesture_management::srv::SaveSequence_Request & msg)
{
  return gesture_management::srv::to_yaml(msg);
}

template<>
inline const char * data_type<gesture_management::srv::SaveSequence_Request>()
{
  return "gesture_management::srv::SaveSequence_Request";
}

template<>
inline const char * name<gesture_management::srv::SaveSequence_Request>()
{
  return "gesture_management/srv/SaveSequence_Request";
}

template<>
struct has_fixed_size<gesture_management::srv::SaveSequence_Request>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<gesture_management::srv::SaveSequence_Request>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<gesture_management::srv::SaveSequence_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace gesture_management
{

namespace srv
{

inline void to_flow_style_yaml(
  const SaveSequence_Response & msg,
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
  const SaveSequence_Response & msg,
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

inline std::string to_yaml(const SaveSequence_Response & msg, bool use_flow_style = false)
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
  const gesture_management::srv::SaveSequence_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  gesture_management::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use gesture_management::srv::to_yaml() instead")]]
inline std::string to_yaml(const gesture_management::srv::SaveSequence_Response & msg)
{
  return gesture_management::srv::to_yaml(msg);
}

template<>
inline const char * data_type<gesture_management::srv::SaveSequence_Response>()
{
  return "gesture_management::srv::SaveSequence_Response";
}

template<>
inline const char * name<gesture_management::srv::SaveSequence_Response>()
{
  return "gesture_management/srv/SaveSequence_Response";
}

template<>
struct has_fixed_size<gesture_management::srv::SaveSequence_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<gesture_management::srv::SaveSequence_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<gesture_management::srv::SaveSequence_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<gesture_management::srv::SaveSequence>()
{
  return "gesture_management::srv::SaveSequence";
}

template<>
inline const char * name<gesture_management::srv::SaveSequence>()
{
  return "gesture_management/srv/SaveSequence";
}

template<>
struct has_fixed_size<gesture_management::srv::SaveSequence>
  : std::integral_constant<
    bool,
    has_fixed_size<gesture_management::srv::SaveSequence_Request>::value &&
    has_fixed_size<gesture_management::srv::SaveSequence_Response>::value
  >
{
};

template<>
struct has_bounded_size<gesture_management::srv::SaveSequence>
  : std::integral_constant<
    bool,
    has_bounded_size<gesture_management::srv::SaveSequence_Request>::value &&
    has_bounded_size<gesture_management::srv::SaveSequence_Response>::value
  >
{
};

template<>
struct is_service<gesture_management::srv::SaveSequence>
  : std::true_type
{
};

template<>
struct is_service_request<gesture_management::srv::SaveSequence_Request>
  : std::true_type
{
};

template<>
struct is_service_response<gesture_management::srv::SaveSequence_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // GESTURE_MANAGEMENT__SRV__DETAIL__SAVE_SEQUENCE__TRAITS_HPP_
