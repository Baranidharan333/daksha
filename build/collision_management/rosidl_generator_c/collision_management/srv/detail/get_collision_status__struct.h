// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from collision_management:srv/GetCollisionStatus.idl
// generated code does not contain a copyright notice

#ifndef COLLISION_MANAGEMENT__SRV__DETAIL__GET_COLLISION_STATUS__STRUCT_H_
#define COLLISION_MANAGEMENT__SRV__DETAIL__GET_COLLISION_STATUS__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in srv/GetCollisionStatus in the package collision_management.
typedef struct collision_management__srv__GetCollisionStatus_Request
{
  uint8_t structure_needs_at_least_one_member;
} collision_management__srv__GetCollisionStatus_Request;

// Struct for a sequence of collision_management__srv__GetCollisionStatus_Request.
typedef struct collision_management__srv__GetCollisionStatus_Request__Sequence
{
  collision_management__srv__GetCollisionStatus_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} collision_management__srv__GetCollisionStatus_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'status'
#include "sensor_msgs/msg/detail/joint_state__struct.h"

/// Struct defined in srv/GetCollisionStatus in the package collision_management.
typedef struct collision_management__srv__GetCollisionStatus_Response
{
  bool in_collision;
  sensor_msgs__msg__JointState status;
} collision_management__srv__GetCollisionStatus_Response;

// Struct for a sequence of collision_management__srv__GetCollisionStatus_Response.
typedef struct collision_management__srv__GetCollisionStatus_Response__Sequence
{
  collision_management__srv__GetCollisionStatus_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} collision_management__srv__GetCollisionStatus_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // COLLISION_MANAGEMENT__SRV__DETAIL__GET_COLLISION_STATUS__STRUCT_H_
