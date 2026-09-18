// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from gesture_management:srv/PlaySequence.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "gesture_management/srv/detail/play_sequence__rosidl_typesupport_introspection_c.h"
#include "gesture_management/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "gesture_management/srv/detail/play_sequence__functions.h"
#include "gesture_management/srv/detail/play_sequence__struct.h"


// Include directives for member types
// Member `sequence_name`
// Member `recording_names`
// Member `output_topic`
// Member `repeat_mode`
#include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__PlaySequence_Request_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  gesture_management__srv__PlaySequence_Request__init(message_memory);
}

void gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__PlaySequence_Request_fini_function(void * message_memory)
{
  gesture_management__srv__PlaySequence_Request__fini(message_memory);
}

size_t gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__size_function__PlaySequence_Request__recording_names(
  const void * untyped_member)
{
  const rosidl_runtime_c__String__Sequence * member =
    (const rosidl_runtime_c__String__Sequence *)(untyped_member);
  return member->size;
}

const void * gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__get_const_function__PlaySequence_Request__recording_names(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__String__Sequence * member =
    (const rosidl_runtime_c__String__Sequence *)(untyped_member);
  return &member->data[index];
}

void * gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__get_function__PlaySequence_Request__recording_names(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__String__Sequence * member =
    (rosidl_runtime_c__String__Sequence *)(untyped_member);
  return &member->data[index];
}

void gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__fetch_function__PlaySequence_Request__recording_names(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const rosidl_runtime_c__String * item =
    ((const rosidl_runtime_c__String *)
    gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__get_const_function__PlaySequence_Request__recording_names(untyped_member, index));
  rosidl_runtime_c__String * value =
    (rosidl_runtime_c__String *)(untyped_value);
  *value = *item;
}

void gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__assign_function__PlaySequence_Request__recording_names(
  void * untyped_member, size_t index, const void * untyped_value)
{
  rosidl_runtime_c__String * item =
    ((rosidl_runtime_c__String *)
    gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__get_function__PlaySequence_Request__recording_names(untyped_member, index));
  const rosidl_runtime_c__String * value =
    (const rosidl_runtime_c__String *)(untyped_value);
  *item = *value;
}

bool gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__resize_function__PlaySequence_Request__recording_names(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__String__Sequence * member =
    (rosidl_runtime_c__String__Sequence *)(untyped_member);
  rosidl_runtime_c__String__Sequence__fini(member);
  return rosidl_runtime_c__String__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__PlaySequence_Request_message_member_array[7] = {
  {
    "sequence_name",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(gesture_management__srv__PlaySequence_Request, sequence_name),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "recording_names",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(gesture_management__srv__PlaySequence_Request, recording_names),  // bytes offset in struct
    NULL,  // default value
    gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__size_function__PlaySequence_Request__recording_names,  // size() function pointer
    gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__get_const_function__PlaySequence_Request__recording_names,  // get_const(index) function pointer
    gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__get_function__PlaySequence_Request__recording_names,  // get(index) function pointer
    gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__fetch_function__PlaySequence_Request__recording_names,  // fetch(index, &value) function pointer
    gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__assign_function__PlaySequence_Request__recording_names,  // assign(index, value) function pointer
    gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__resize_function__PlaySequence_Request__recording_names  // resize(index) function pointer
  },
  {
    "output_topic",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(gesture_management__srv__PlaySequence_Request, output_topic),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "replay_speed",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(gesture_management__srv__PlaySequence_Request, replay_speed),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "repeat_mode",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(gesture_management__srv__PlaySequence_Request, repeat_mode),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "repeat_count",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(gesture_management__srv__PlaySequence_Request, repeat_count),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "interval_s",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(gesture_management__srv__PlaySequence_Request, interval_s),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__PlaySequence_Request_message_members = {
  "gesture_management__srv",  // message namespace
  "PlaySequence_Request",  // message name
  7,  // number of fields
  sizeof(gesture_management__srv__PlaySequence_Request),
  gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__PlaySequence_Request_message_member_array,  // message members
  gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__PlaySequence_Request_init_function,  // function to initialize message memory (memory has to be allocated)
  gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__PlaySequence_Request_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__PlaySequence_Request_message_type_support_handle = {
  0,
  &gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__PlaySequence_Request_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_gesture_management
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, gesture_management, srv, PlaySequence_Request)() {
  if (!gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__PlaySequence_Request_message_type_support_handle.typesupport_identifier) {
    gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__PlaySequence_Request_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &gesture_management__srv__PlaySequence_Request__rosidl_typesupport_introspection_c__PlaySequence_Request_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

// already included above
// #include <stddef.h>
// already included above
// #include "gesture_management/srv/detail/play_sequence__rosidl_typesupport_introspection_c.h"
// already included above
// #include "gesture_management/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "rosidl_typesupport_introspection_c/field_types.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
// already included above
// #include "rosidl_typesupport_introspection_c/message_introspection.h"
// already included above
// #include "gesture_management/srv/detail/play_sequence__functions.h"
// already included above
// #include "gesture_management/srv/detail/play_sequence__struct.h"


// Include directives for member types
// Member `message`
// already included above
// #include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void gesture_management__srv__PlaySequence_Response__rosidl_typesupport_introspection_c__PlaySequence_Response_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  gesture_management__srv__PlaySequence_Response__init(message_memory);
}

void gesture_management__srv__PlaySequence_Response__rosidl_typesupport_introspection_c__PlaySequence_Response_fini_function(void * message_memory)
{
  gesture_management__srv__PlaySequence_Response__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember gesture_management__srv__PlaySequence_Response__rosidl_typesupport_introspection_c__PlaySequence_Response_message_member_array[2] = {
  {
    "success",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(gesture_management__srv__PlaySequence_Response, success),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "message",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(gesture_management__srv__PlaySequence_Response, message),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers gesture_management__srv__PlaySequence_Response__rosidl_typesupport_introspection_c__PlaySequence_Response_message_members = {
  "gesture_management__srv",  // message namespace
  "PlaySequence_Response",  // message name
  2,  // number of fields
  sizeof(gesture_management__srv__PlaySequence_Response),
  gesture_management__srv__PlaySequence_Response__rosidl_typesupport_introspection_c__PlaySequence_Response_message_member_array,  // message members
  gesture_management__srv__PlaySequence_Response__rosidl_typesupport_introspection_c__PlaySequence_Response_init_function,  // function to initialize message memory (memory has to be allocated)
  gesture_management__srv__PlaySequence_Response__rosidl_typesupport_introspection_c__PlaySequence_Response_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t gesture_management__srv__PlaySequence_Response__rosidl_typesupport_introspection_c__PlaySequence_Response_message_type_support_handle = {
  0,
  &gesture_management__srv__PlaySequence_Response__rosidl_typesupport_introspection_c__PlaySequence_Response_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_gesture_management
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, gesture_management, srv, PlaySequence_Response)() {
  if (!gesture_management__srv__PlaySequence_Response__rosidl_typesupport_introspection_c__PlaySequence_Response_message_type_support_handle.typesupport_identifier) {
    gesture_management__srv__PlaySequence_Response__rosidl_typesupport_introspection_c__PlaySequence_Response_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &gesture_management__srv__PlaySequence_Response__rosidl_typesupport_introspection_c__PlaySequence_Response_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "gesture_management/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "gesture_management/srv/detail/play_sequence__rosidl_typesupport_introspection_c.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/service_introspection.h"

// this is intentionally not const to allow initialization later to prevent an initialization race
static rosidl_typesupport_introspection_c__ServiceMembers gesture_management__srv__detail__play_sequence__rosidl_typesupport_introspection_c__PlaySequence_service_members = {
  "gesture_management__srv",  // service namespace
  "PlaySequence",  // service name
  // these two fields are initialized below on the first access
  NULL,  // request message
  // gesture_management__srv__detail__play_sequence__rosidl_typesupport_introspection_c__PlaySequence_Request_message_type_support_handle,
  NULL  // response message
  // gesture_management__srv__detail__play_sequence__rosidl_typesupport_introspection_c__PlaySequence_Response_message_type_support_handle
};

static rosidl_service_type_support_t gesture_management__srv__detail__play_sequence__rosidl_typesupport_introspection_c__PlaySequence_service_type_support_handle = {
  0,
  &gesture_management__srv__detail__play_sequence__rosidl_typesupport_introspection_c__PlaySequence_service_members,
  get_service_typesupport_handle_function,
};

// Forward declaration of request/response type support functions
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, gesture_management, srv, PlaySequence_Request)();

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, gesture_management, srv, PlaySequence_Response)();

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_gesture_management
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_c, gesture_management, srv, PlaySequence)() {
  if (!gesture_management__srv__detail__play_sequence__rosidl_typesupport_introspection_c__PlaySequence_service_type_support_handle.typesupport_identifier) {
    gesture_management__srv__detail__play_sequence__rosidl_typesupport_introspection_c__PlaySequence_service_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  rosidl_typesupport_introspection_c__ServiceMembers * service_members =
    (rosidl_typesupport_introspection_c__ServiceMembers *)gesture_management__srv__detail__play_sequence__rosidl_typesupport_introspection_c__PlaySequence_service_type_support_handle.data;

  if (!service_members->request_members_) {
    service_members->request_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, gesture_management, srv, PlaySequence_Request)()->data;
  }
  if (!service_members->response_members_) {
    service_members->response_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, gesture_management, srv, PlaySequence_Response)()->data;
  }

  return &gesture_management__srv__detail__play_sequence__rosidl_typesupport_introspection_c__PlaySequence_service_type_support_handle;
}
