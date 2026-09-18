// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from gesture_management:srv/ReplayRecording.idl
// generated code does not contain a copyright notice

#ifndef GESTURE_MANAGEMENT__SRV__DETAIL__REPLAY_RECORDING__FUNCTIONS_H_
#define GESTURE_MANAGEMENT__SRV__DETAIL__REPLAY_RECORDING__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "gesture_management/msg/rosidl_generator_c__visibility_control.h"

#include "gesture_management/srv/detail/replay_recording__struct.h"

/// Initialize srv/ReplayRecording message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * gesture_management__srv__ReplayRecording_Request
 * )) before or use
 * gesture_management__srv__ReplayRecording_Request__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
bool
gesture_management__srv__ReplayRecording_Request__init(gesture_management__srv__ReplayRecording_Request * msg);

/// Finalize srv/ReplayRecording message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
void
gesture_management__srv__ReplayRecording_Request__fini(gesture_management__srv__ReplayRecording_Request * msg);

/// Create srv/ReplayRecording message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * gesture_management__srv__ReplayRecording_Request__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
gesture_management__srv__ReplayRecording_Request *
gesture_management__srv__ReplayRecording_Request__create();

/// Destroy srv/ReplayRecording message.
/**
 * It calls
 * gesture_management__srv__ReplayRecording_Request__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
void
gesture_management__srv__ReplayRecording_Request__destroy(gesture_management__srv__ReplayRecording_Request * msg);

/// Check for srv/ReplayRecording message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
bool
gesture_management__srv__ReplayRecording_Request__are_equal(const gesture_management__srv__ReplayRecording_Request * lhs, const gesture_management__srv__ReplayRecording_Request * rhs);

/// Copy a srv/ReplayRecording message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
bool
gesture_management__srv__ReplayRecording_Request__copy(
  const gesture_management__srv__ReplayRecording_Request * input,
  gesture_management__srv__ReplayRecording_Request * output);

/// Initialize array of srv/ReplayRecording messages.
/**
 * It allocates the memory for the number of elements and calls
 * gesture_management__srv__ReplayRecording_Request__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
bool
gesture_management__srv__ReplayRecording_Request__Sequence__init(gesture_management__srv__ReplayRecording_Request__Sequence * array, size_t size);

/// Finalize array of srv/ReplayRecording messages.
/**
 * It calls
 * gesture_management__srv__ReplayRecording_Request__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
void
gesture_management__srv__ReplayRecording_Request__Sequence__fini(gesture_management__srv__ReplayRecording_Request__Sequence * array);

/// Create array of srv/ReplayRecording messages.
/**
 * It allocates the memory for the array and calls
 * gesture_management__srv__ReplayRecording_Request__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
gesture_management__srv__ReplayRecording_Request__Sequence *
gesture_management__srv__ReplayRecording_Request__Sequence__create(size_t size);

/// Destroy array of srv/ReplayRecording messages.
/**
 * It calls
 * gesture_management__srv__ReplayRecording_Request__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
void
gesture_management__srv__ReplayRecording_Request__Sequence__destroy(gesture_management__srv__ReplayRecording_Request__Sequence * array);

/// Check for srv/ReplayRecording message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
bool
gesture_management__srv__ReplayRecording_Request__Sequence__are_equal(const gesture_management__srv__ReplayRecording_Request__Sequence * lhs, const gesture_management__srv__ReplayRecording_Request__Sequence * rhs);

/// Copy an array of srv/ReplayRecording messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
bool
gesture_management__srv__ReplayRecording_Request__Sequence__copy(
  const gesture_management__srv__ReplayRecording_Request__Sequence * input,
  gesture_management__srv__ReplayRecording_Request__Sequence * output);

/// Initialize srv/ReplayRecording message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * gesture_management__srv__ReplayRecording_Response
 * )) before or use
 * gesture_management__srv__ReplayRecording_Response__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
bool
gesture_management__srv__ReplayRecording_Response__init(gesture_management__srv__ReplayRecording_Response * msg);

/// Finalize srv/ReplayRecording message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
void
gesture_management__srv__ReplayRecording_Response__fini(gesture_management__srv__ReplayRecording_Response * msg);

/// Create srv/ReplayRecording message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * gesture_management__srv__ReplayRecording_Response__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
gesture_management__srv__ReplayRecording_Response *
gesture_management__srv__ReplayRecording_Response__create();

/// Destroy srv/ReplayRecording message.
/**
 * It calls
 * gesture_management__srv__ReplayRecording_Response__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
void
gesture_management__srv__ReplayRecording_Response__destroy(gesture_management__srv__ReplayRecording_Response * msg);

/// Check for srv/ReplayRecording message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
bool
gesture_management__srv__ReplayRecording_Response__are_equal(const gesture_management__srv__ReplayRecording_Response * lhs, const gesture_management__srv__ReplayRecording_Response * rhs);

/// Copy a srv/ReplayRecording message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
bool
gesture_management__srv__ReplayRecording_Response__copy(
  const gesture_management__srv__ReplayRecording_Response * input,
  gesture_management__srv__ReplayRecording_Response * output);

/// Initialize array of srv/ReplayRecording messages.
/**
 * It allocates the memory for the number of elements and calls
 * gesture_management__srv__ReplayRecording_Response__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
bool
gesture_management__srv__ReplayRecording_Response__Sequence__init(gesture_management__srv__ReplayRecording_Response__Sequence * array, size_t size);

/// Finalize array of srv/ReplayRecording messages.
/**
 * It calls
 * gesture_management__srv__ReplayRecording_Response__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
void
gesture_management__srv__ReplayRecording_Response__Sequence__fini(gesture_management__srv__ReplayRecording_Response__Sequence * array);

/// Create array of srv/ReplayRecording messages.
/**
 * It allocates the memory for the array and calls
 * gesture_management__srv__ReplayRecording_Response__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
gesture_management__srv__ReplayRecording_Response__Sequence *
gesture_management__srv__ReplayRecording_Response__Sequence__create(size_t size);

/// Destroy array of srv/ReplayRecording messages.
/**
 * It calls
 * gesture_management__srv__ReplayRecording_Response__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
void
gesture_management__srv__ReplayRecording_Response__Sequence__destroy(gesture_management__srv__ReplayRecording_Response__Sequence * array);

/// Check for srv/ReplayRecording message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
bool
gesture_management__srv__ReplayRecording_Response__Sequence__are_equal(const gesture_management__srv__ReplayRecording_Response__Sequence * lhs, const gesture_management__srv__ReplayRecording_Response__Sequence * rhs);

/// Copy an array of srv/ReplayRecording messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_gesture_management
bool
gesture_management__srv__ReplayRecording_Response__Sequence__copy(
  const gesture_management__srv__ReplayRecording_Response__Sequence * input,
  gesture_management__srv__ReplayRecording_Response__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // GESTURE_MANAGEMENT__SRV__DETAIL__REPLAY_RECORDING__FUNCTIONS_H_
