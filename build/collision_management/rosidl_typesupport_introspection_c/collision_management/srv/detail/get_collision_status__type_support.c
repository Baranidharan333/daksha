// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from collision_management:srv/GetCollisionStatus.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "collision_management/srv/detail/get_collision_status__rosidl_typesupport_introspection_c.h"
#include "collision_management/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "collision_management/srv/detail/get_collision_status__functions.h"
#include "collision_management/srv/detail/get_collision_status__struct.h"


#ifdef __cplusplus
extern "C"
{
#endif

void collision_management__srv__GetCollisionStatus_Request__rosidl_typesupport_introspection_c__GetCollisionStatus_Request_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  collision_management__srv__GetCollisionStatus_Request__init(message_memory);
}

void collision_management__srv__GetCollisionStatus_Request__rosidl_typesupport_introspection_c__GetCollisionStatus_Request_fini_function(void * message_memory)
{
  collision_management__srv__GetCollisionStatus_Request__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember collision_management__srv__GetCollisionStatus_Request__rosidl_typesupport_introspection_c__GetCollisionStatus_Request_message_member_array[1] = {
  {
    "structure_needs_at_least_one_member",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(collision_management__srv__GetCollisionStatus_Request, structure_needs_at_least_one_member),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers collision_management__srv__GetCollisionStatus_Request__rosidl_typesupport_introspection_c__GetCollisionStatus_Request_message_members = {
  "collision_management__srv",  // message namespace
  "GetCollisionStatus_Request",  // message name
  1,  // number of fields
  sizeof(collision_management__srv__GetCollisionStatus_Request),
  collision_management__srv__GetCollisionStatus_Request__rosidl_typesupport_introspection_c__GetCollisionStatus_Request_message_member_array,  // message members
  collision_management__srv__GetCollisionStatus_Request__rosidl_typesupport_introspection_c__GetCollisionStatus_Request_init_function,  // function to initialize message memory (memory has to be allocated)
  collision_management__srv__GetCollisionStatus_Request__rosidl_typesupport_introspection_c__GetCollisionStatus_Request_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t collision_management__srv__GetCollisionStatus_Request__rosidl_typesupport_introspection_c__GetCollisionStatus_Request_message_type_support_handle = {
  0,
  &collision_management__srv__GetCollisionStatus_Request__rosidl_typesupport_introspection_c__GetCollisionStatus_Request_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_collision_management
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, collision_management, srv, GetCollisionStatus_Request)() {
  if (!collision_management__srv__GetCollisionStatus_Request__rosidl_typesupport_introspection_c__GetCollisionStatus_Request_message_type_support_handle.typesupport_identifier) {
    collision_management__srv__GetCollisionStatus_Request__rosidl_typesupport_introspection_c__GetCollisionStatus_Request_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &collision_management__srv__GetCollisionStatus_Request__rosidl_typesupport_introspection_c__GetCollisionStatus_Request_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

// already included above
// #include <stddef.h>
// already included above
// #include "collision_management/srv/detail/get_collision_status__rosidl_typesupport_introspection_c.h"
// already included above
// #include "collision_management/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "rosidl_typesupport_introspection_c/field_types.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
// already included above
// #include "rosidl_typesupport_introspection_c/message_introspection.h"
// already included above
// #include "collision_management/srv/detail/get_collision_status__functions.h"
// already included above
// #include "collision_management/srv/detail/get_collision_status__struct.h"


// Include directives for member types
// Member `status`
#include "sensor_msgs/msg/joint_state.h"
// Member `status`
#include "sensor_msgs/msg/detail/joint_state__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void collision_management__srv__GetCollisionStatus_Response__rosidl_typesupport_introspection_c__GetCollisionStatus_Response_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  collision_management__srv__GetCollisionStatus_Response__init(message_memory);
}

void collision_management__srv__GetCollisionStatus_Response__rosidl_typesupport_introspection_c__GetCollisionStatus_Response_fini_function(void * message_memory)
{
  collision_management__srv__GetCollisionStatus_Response__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember collision_management__srv__GetCollisionStatus_Response__rosidl_typesupport_introspection_c__GetCollisionStatus_Response_message_member_array[2] = {
  {
    "in_collision",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(collision_management__srv__GetCollisionStatus_Response, in_collision),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "status",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(collision_management__srv__GetCollisionStatus_Response, status),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers collision_management__srv__GetCollisionStatus_Response__rosidl_typesupport_introspection_c__GetCollisionStatus_Response_message_members = {
  "collision_management__srv",  // message namespace
  "GetCollisionStatus_Response",  // message name
  2,  // number of fields
  sizeof(collision_management__srv__GetCollisionStatus_Response),
  collision_management__srv__GetCollisionStatus_Response__rosidl_typesupport_introspection_c__GetCollisionStatus_Response_message_member_array,  // message members
  collision_management__srv__GetCollisionStatus_Response__rosidl_typesupport_introspection_c__GetCollisionStatus_Response_init_function,  // function to initialize message memory (memory has to be allocated)
  collision_management__srv__GetCollisionStatus_Response__rosidl_typesupport_introspection_c__GetCollisionStatus_Response_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t collision_management__srv__GetCollisionStatus_Response__rosidl_typesupport_introspection_c__GetCollisionStatus_Response_message_type_support_handle = {
  0,
  &collision_management__srv__GetCollisionStatus_Response__rosidl_typesupport_introspection_c__GetCollisionStatus_Response_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_collision_management
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, collision_management, srv, GetCollisionStatus_Response)() {
  collision_management__srv__GetCollisionStatus_Response__rosidl_typesupport_introspection_c__GetCollisionStatus_Response_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, sensor_msgs, msg, JointState)();
  if (!collision_management__srv__GetCollisionStatus_Response__rosidl_typesupport_introspection_c__GetCollisionStatus_Response_message_type_support_handle.typesupport_identifier) {
    collision_management__srv__GetCollisionStatus_Response__rosidl_typesupport_introspection_c__GetCollisionStatus_Response_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &collision_management__srv__GetCollisionStatus_Response__rosidl_typesupport_introspection_c__GetCollisionStatus_Response_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "collision_management/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "collision_management/srv/detail/get_collision_status__rosidl_typesupport_introspection_c.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/service_introspection.h"

// this is intentionally not const to allow initialization later to prevent an initialization race
static rosidl_typesupport_introspection_c__ServiceMembers collision_management__srv__detail__get_collision_status__rosidl_typesupport_introspection_c__GetCollisionStatus_service_members = {
  "collision_management__srv",  // service namespace
  "GetCollisionStatus",  // service name
  // these two fields are initialized below on the first access
  NULL,  // request message
  // collision_management__srv__detail__get_collision_status__rosidl_typesupport_introspection_c__GetCollisionStatus_Request_message_type_support_handle,
  NULL  // response message
  // collision_management__srv__detail__get_collision_status__rosidl_typesupport_introspection_c__GetCollisionStatus_Response_message_type_support_handle
};

static rosidl_service_type_support_t collision_management__srv__detail__get_collision_status__rosidl_typesupport_introspection_c__GetCollisionStatus_service_type_support_handle = {
  0,
  &collision_management__srv__detail__get_collision_status__rosidl_typesupport_introspection_c__GetCollisionStatus_service_members,
  get_service_typesupport_handle_function,
};

// Forward declaration of request/response type support functions
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, collision_management, srv, GetCollisionStatus_Request)();

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, collision_management, srv, GetCollisionStatus_Response)();

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_collision_management
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_c, collision_management, srv, GetCollisionStatus)() {
  if (!collision_management__srv__detail__get_collision_status__rosidl_typesupport_introspection_c__GetCollisionStatus_service_type_support_handle.typesupport_identifier) {
    collision_management__srv__detail__get_collision_status__rosidl_typesupport_introspection_c__GetCollisionStatus_service_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  rosidl_typesupport_introspection_c__ServiceMembers * service_members =
    (rosidl_typesupport_introspection_c__ServiceMembers *)collision_management__srv__detail__get_collision_status__rosidl_typesupport_introspection_c__GetCollisionStatus_service_type_support_handle.data;

  if (!service_members->request_members_) {
    service_members->request_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, collision_management, srv, GetCollisionStatus_Request)()->data;
  }
  if (!service_members->response_members_) {
    service_members->response_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, collision_management, srv, GetCollisionStatus_Response)()->data;
  }

  return &collision_management__srv__detail__get_collision_status__rosidl_typesupport_introspection_c__GetCollisionStatus_service_type_support_handle;
}
