// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from hw_interface:srv/SetMotorGains.idl
// generated code does not contain a copyright notice

#ifndef HW_INTERFACE__SRV__DETAIL__SET_MOTOR_GAINS__FUNCTIONS_H_
#define HW_INTERFACE__SRV__DETAIL__SET_MOTOR_GAINS__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "hw_interface/msg/rosidl_generator_c__visibility_control.h"

#include "hw_interface/srv/detail/set_motor_gains__struct.h"

/// Initialize srv/SetMotorGains message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * hw_interface__srv__SetMotorGains_Request
 * )) before or use
 * hw_interface__srv__SetMotorGains_Request__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
bool
hw_interface__srv__SetMotorGains_Request__init(hw_interface__srv__SetMotorGains_Request * msg);

/// Finalize srv/SetMotorGains message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
void
hw_interface__srv__SetMotorGains_Request__fini(hw_interface__srv__SetMotorGains_Request * msg);

/// Create srv/SetMotorGains message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * hw_interface__srv__SetMotorGains_Request__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
hw_interface__srv__SetMotorGains_Request *
hw_interface__srv__SetMotorGains_Request__create();

/// Destroy srv/SetMotorGains message.
/**
 * It calls
 * hw_interface__srv__SetMotorGains_Request__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
void
hw_interface__srv__SetMotorGains_Request__destroy(hw_interface__srv__SetMotorGains_Request * msg);

/// Check for srv/SetMotorGains message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
bool
hw_interface__srv__SetMotorGains_Request__are_equal(const hw_interface__srv__SetMotorGains_Request * lhs, const hw_interface__srv__SetMotorGains_Request * rhs);

/// Copy a srv/SetMotorGains message.
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
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
bool
hw_interface__srv__SetMotorGains_Request__copy(
  const hw_interface__srv__SetMotorGains_Request * input,
  hw_interface__srv__SetMotorGains_Request * output);

/// Initialize array of srv/SetMotorGains messages.
/**
 * It allocates the memory for the number of elements and calls
 * hw_interface__srv__SetMotorGains_Request__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
bool
hw_interface__srv__SetMotorGains_Request__Sequence__init(hw_interface__srv__SetMotorGains_Request__Sequence * array, size_t size);

/// Finalize array of srv/SetMotorGains messages.
/**
 * It calls
 * hw_interface__srv__SetMotorGains_Request__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
void
hw_interface__srv__SetMotorGains_Request__Sequence__fini(hw_interface__srv__SetMotorGains_Request__Sequence * array);

/// Create array of srv/SetMotorGains messages.
/**
 * It allocates the memory for the array and calls
 * hw_interface__srv__SetMotorGains_Request__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
hw_interface__srv__SetMotorGains_Request__Sequence *
hw_interface__srv__SetMotorGains_Request__Sequence__create(size_t size);

/// Destroy array of srv/SetMotorGains messages.
/**
 * It calls
 * hw_interface__srv__SetMotorGains_Request__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
void
hw_interface__srv__SetMotorGains_Request__Sequence__destroy(hw_interface__srv__SetMotorGains_Request__Sequence * array);

/// Check for srv/SetMotorGains message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
bool
hw_interface__srv__SetMotorGains_Request__Sequence__are_equal(const hw_interface__srv__SetMotorGains_Request__Sequence * lhs, const hw_interface__srv__SetMotorGains_Request__Sequence * rhs);

/// Copy an array of srv/SetMotorGains messages.
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
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
bool
hw_interface__srv__SetMotorGains_Request__Sequence__copy(
  const hw_interface__srv__SetMotorGains_Request__Sequence * input,
  hw_interface__srv__SetMotorGains_Request__Sequence * output);

/// Initialize srv/SetMotorGains message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * hw_interface__srv__SetMotorGains_Response
 * )) before or use
 * hw_interface__srv__SetMotorGains_Response__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
bool
hw_interface__srv__SetMotorGains_Response__init(hw_interface__srv__SetMotorGains_Response * msg);

/// Finalize srv/SetMotorGains message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
void
hw_interface__srv__SetMotorGains_Response__fini(hw_interface__srv__SetMotorGains_Response * msg);

/// Create srv/SetMotorGains message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * hw_interface__srv__SetMotorGains_Response__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
hw_interface__srv__SetMotorGains_Response *
hw_interface__srv__SetMotorGains_Response__create();

/// Destroy srv/SetMotorGains message.
/**
 * It calls
 * hw_interface__srv__SetMotorGains_Response__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
void
hw_interface__srv__SetMotorGains_Response__destroy(hw_interface__srv__SetMotorGains_Response * msg);

/// Check for srv/SetMotorGains message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
bool
hw_interface__srv__SetMotorGains_Response__are_equal(const hw_interface__srv__SetMotorGains_Response * lhs, const hw_interface__srv__SetMotorGains_Response * rhs);

/// Copy a srv/SetMotorGains message.
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
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
bool
hw_interface__srv__SetMotorGains_Response__copy(
  const hw_interface__srv__SetMotorGains_Response * input,
  hw_interface__srv__SetMotorGains_Response * output);

/// Initialize array of srv/SetMotorGains messages.
/**
 * It allocates the memory for the number of elements and calls
 * hw_interface__srv__SetMotorGains_Response__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
bool
hw_interface__srv__SetMotorGains_Response__Sequence__init(hw_interface__srv__SetMotorGains_Response__Sequence * array, size_t size);

/// Finalize array of srv/SetMotorGains messages.
/**
 * It calls
 * hw_interface__srv__SetMotorGains_Response__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
void
hw_interface__srv__SetMotorGains_Response__Sequence__fini(hw_interface__srv__SetMotorGains_Response__Sequence * array);

/// Create array of srv/SetMotorGains messages.
/**
 * It allocates the memory for the array and calls
 * hw_interface__srv__SetMotorGains_Response__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
hw_interface__srv__SetMotorGains_Response__Sequence *
hw_interface__srv__SetMotorGains_Response__Sequence__create(size_t size);

/// Destroy array of srv/SetMotorGains messages.
/**
 * It calls
 * hw_interface__srv__SetMotorGains_Response__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
void
hw_interface__srv__SetMotorGains_Response__Sequence__destroy(hw_interface__srv__SetMotorGains_Response__Sequence * array);

/// Check for srv/SetMotorGains message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
bool
hw_interface__srv__SetMotorGains_Response__Sequence__are_equal(const hw_interface__srv__SetMotorGains_Response__Sequence * lhs, const hw_interface__srv__SetMotorGains_Response__Sequence * rhs);

/// Copy an array of srv/SetMotorGains messages.
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
ROSIDL_GENERATOR_C_PUBLIC_hw_interface
bool
hw_interface__srv__SetMotorGains_Response__Sequence__copy(
  const hw_interface__srv__SetMotorGains_Response__Sequence * input,
  hw_interface__srv__SetMotorGains_Response__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // HW_INTERFACE__SRV__DETAIL__SET_MOTOR_GAINS__FUNCTIONS_H_
