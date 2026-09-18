// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from gesture_management:srv/ReplayRecording.idl
// generated code does not contain a copyright notice

#ifndef GESTURE_MANAGEMENT__SRV__DETAIL__REPLAY_RECORDING__STRUCT_H_
#define GESTURE_MANAGEMENT__SRV__DETAIL__REPLAY_RECORDING__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'recording_name'
// Member 'output_topic'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/ReplayRecording in the package gesture_management.
typedef struct gesture_management__srv__ReplayRecording_Request
{
  rosidl_runtime_c__String recording_name;
  rosidl_runtime_c__String output_topic;
  float replay_speed;
} gesture_management__srv__ReplayRecording_Request;

// Struct for a sequence of gesture_management__srv__ReplayRecording_Request.
typedef struct gesture_management__srv__ReplayRecording_Request__Sequence
{
  gesture_management__srv__ReplayRecording_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} gesture_management__srv__ReplayRecording_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'message'
// already included above
// #include "rosidl_runtime_c/string.h"

/// Struct defined in srv/ReplayRecording in the package gesture_management.
typedef struct gesture_management__srv__ReplayRecording_Response
{
  bool success;
  rosidl_runtime_c__String message;
} gesture_management__srv__ReplayRecording_Response;

// Struct for a sequence of gesture_management__srv__ReplayRecording_Response.
typedef struct gesture_management__srv__ReplayRecording_Response__Sequence
{
  gesture_management__srv__ReplayRecording_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} gesture_management__srv__ReplayRecording_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GESTURE_MANAGEMENT__SRV__DETAIL__REPLAY_RECORDING__STRUCT_H_
