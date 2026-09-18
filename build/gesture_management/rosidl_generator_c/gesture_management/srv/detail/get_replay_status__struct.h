// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from gesture_management:srv/GetReplayStatus.idl
// generated code does not contain a copyright notice

#ifndef GESTURE_MANAGEMENT__SRV__DETAIL__GET_REPLAY_STATUS__STRUCT_H_
#define GESTURE_MANAGEMENT__SRV__DETAIL__GET_REPLAY_STATUS__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in srv/GetReplayStatus in the package gesture_management.
typedef struct gesture_management__srv__GetReplayStatus_Request
{
  uint8_t structure_needs_at_least_one_member;
} gesture_management__srv__GetReplayStatus_Request;

// Struct for a sequence of gesture_management__srv__GetReplayStatus_Request.
typedef struct gesture_management__srv__GetReplayStatus_Request__Sequence
{
  gesture_management__srv__GetReplayStatus_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} gesture_management__srv__GetReplayStatus_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'status_json'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/GetReplayStatus in the package gesture_management.
typedef struct gesture_management__srv__GetReplayStatus_Response
{
  bool success;
  rosidl_runtime_c__String status_json;
} gesture_management__srv__GetReplayStatus_Response;

// Struct for a sequence of gesture_management__srv__GetReplayStatus_Response.
typedef struct gesture_management__srv__GetReplayStatus_Response__Sequence
{
  gesture_management__srv__GetReplayStatus_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} gesture_management__srv__GetReplayStatus_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GESTURE_MANAGEMENT__SRV__DETAIL__GET_REPLAY_STATUS__STRUCT_H_
