// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from daksha_msgs:srv/StartRecord.idl
// generated code does not contain a copyright notice

#ifndef DAKSHA_MSGS__SRV__DETAIL__START_RECORD__STRUCT_H_
#define DAKSHA_MSGS__SRV__DETAIL__START_RECORD__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'dataset_name'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/StartRecord in the package daksha_msgs.
typedef struct daksha_msgs__srv__StartRecord_Request
{
  rosidl_runtime_c__String dataset_name;
  int32_t episode_length;
  float record_hz;
  int32_t max_episodes;
} daksha_msgs__srv__StartRecord_Request;

// Struct for a sequence of daksha_msgs__srv__StartRecord_Request.
typedef struct daksha_msgs__srv__StartRecord_Request__Sequence
{
  daksha_msgs__srv__StartRecord_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} daksha_msgs__srv__StartRecord_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'message'
// already included above
// #include "rosidl_runtime_c/string.h"

/// Struct defined in srv/StartRecord in the package daksha_msgs.
typedef struct daksha_msgs__srv__StartRecord_Response
{
  bool success;
  rosidl_runtime_c__String message;
} daksha_msgs__srv__StartRecord_Response;

// Struct for a sequence of daksha_msgs__srv__StartRecord_Response.
typedef struct daksha_msgs__srv__StartRecord_Response__Sequence
{
  daksha_msgs__srv__StartRecord_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} daksha_msgs__srv__StartRecord_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // DAKSHA_MSGS__SRV__DETAIL__START_RECORD__STRUCT_H_
