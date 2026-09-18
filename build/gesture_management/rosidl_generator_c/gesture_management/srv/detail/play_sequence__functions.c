// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from gesture_management:srv/PlaySequence.idl
// generated code does not contain a copyright notice
#include "gesture_management/srv/detail/play_sequence__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

// Include directives for member types
// Member `sequence_name`
// Member `recording_names`
// Member `output_topic`
// Member `repeat_mode`
#include "rosidl_runtime_c/string_functions.h"

bool
gesture_management__srv__PlaySequence_Request__init(gesture_management__srv__PlaySequence_Request * msg)
{
  if (!msg) {
    return false;
  }
  // sequence_name
  if (!rosidl_runtime_c__String__init(&msg->sequence_name)) {
    gesture_management__srv__PlaySequence_Request__fini(msg);
    return false;
  }
  // recording_names
  if (!rosidl_runtime_c__String__Sequence__init(&msg->recording_names, 0)) {
    gesture_management__srv__PlaySequence_Request__fini(msg);
    return false;
  }
  // output_topic
  if (!rosidl_runtime_c__String__init(&msg->output_topic)) {
    gesture_management__srv__PlaySequence_Request__fini(msg);
    return false;
  }
  // replay_speed
  // repeat_mode
  if (!rosidl_runtime_c__String__init(&msg->repeat_mode)) {
    gesture_management__srv__PlaySequence_Request__fini(msg);
    return false;
  }
  // repeat_count
  // interval_s
  return true;
}

void
gesture_management__srv__PlaySequence_Request__fini(gesture_management__srv__PlaySequence_Request * msg)
{
  if (!msg) {
    return;
  }
  // sequence_name
  rosidl_runtime_c__String__fini(&msg->sequence_name);
  // recording_names
  rosidl_runtime_c__String__Sequence__fini(&msg->recording_names);
  // output_topic
  rosidl_runtime_c__String__fini(&msg->output_topic);
  // replay_speed
  // repeat_mode
  rosidl_runtime_c__String__fini(&msg->repeat_mode);
  // repeat_count
  // interval_s
}

bool
gesture_management__srv__PlaySequence_Request__are_equal(const gesture_management__srv__PlaySequence_Request * lhs, const gesture_management__srv__PlaySequence_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // sequence_name
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->sequence_name), &(rhs->sequence_name)))
  {
    return false;
  }
  // recording_names
  if (!rosidl_runtime_c__String__Sequence__are_equal(
      &(lhs->recording_names), &(rhs->recording_names)))
  {
    return false;
  }
  // output_topic
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->output_topic), &(rhs->output_topic)))
  {
    return false;
  }
  // replay_speed
  if (lhs->replay_speed != rhs->replay_speed) {
    return false;
  }
  // repeat_mode
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->repeat_mode), &(rhs->repeat_mode)))
  {
    return false;
  }
  // repeat_count
  if (lhs->repeat_count != rhs->repeat_count) {
    return false;
  }
  // interval_s
  if (lhs->interval_s != rhs->interval_s) {
    return false;
  }
  return true;
}

bool
gesture_management__srv__PlaySequence_Request__copy(
  const gesture_management__srv__PlaySequence_Request * input,
  gesture_management__srv__PlaySequence_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // sequence_name
  if (!rosidl_runtime_c__String__copy(
      &(input->sequence_name), &(output->sequence_name)))
  {
    return false;
  }
  // recording_names
  if (!rosidl_runtime_c__String__Sequence__copy(
      &(input->recording_names), &(output->recording_names)))
  {
    return false;
  }
  // output_topic
  if (!rosidl_runtime_c__String__copy(
      &(input->output_topic), &(output->output_topic)))
  {
    return false;
  }
  // replay_speed
  output->replay_speed = input->replay_speed;
  // repeat_mode
  if (!rosidl_runtime_c__String__copy(
      &(input->repeat_mode), &(output->repeat_mode)))
  {
    return false;
  }
  // repeat_count
  output->repeat_count = input->repeat_count;
  // interval_s
  output->interval_s = input->interval_s;
  return true;
}

gesture_management__srv__PlaySequence_Request *
gesture_management__srv__PlaySequence_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  gesture_management__srv__PlaySequence_Request * msg = (gesture_management__srv__PlaySequence_Request *)allocator.allocate(sizeof(gesture_management__srv__PlaySequence_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(gesture_management__srv__PlaySequence_Request));
  bool success = gesture_management__srv__PlaySequence_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
gesture_management__srv__PlaySequence_Request__destroy(gesture_management__srv__PlaySequence_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    gesture_management__srv__PlaySequence_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
gesture_management__srv__PlaySequence_Request__Sequence__init(gesture_management__srv__PlaySequence_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  gesture_management__srv__PlaySequence_Request * data = NULL;

  if (size) {
    data = (gesture_management__srv__PlaySequence_Request *)allocator.zero_allocate(size, sizeof(gesture_management__srv__PlaySequence_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = gesture_management__srv__PlaySequence_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        gesture_management__srv__PlaySequence_Request__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
gesture_management__srv__PlaySequence_Request__Sequence__fini(gesture_management__srv__PlaySequence_Request__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      gesture_management__srv__PlaySequence_Request__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

gesture_management__srv__PlaySequence_Request__Sequence *
gesture_management__srv__PlaySequence_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  gesture_management__srv__PlaySequence_Request__Sequence * array = (gesture_management__srv__PlaySequence_Request__Sequence *)allocator.allocate(sizeof(gesture_management__srv__PlaySequence_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = gesture_management__srv__PlaySequence_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
gesture_management__srv__PlaySequence_Request__Sequence__destroy(gesture_management__srv__PlaySequence_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    gesture_management__srv__PlaySequence_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
gesture_management__srv__PlaySequence_Request__Sequence__are_equal(const gesture_management__srv__PlaySequence_Request__Sequence * lhs, const gesture_management__srv__PlaySequence_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!gesture_management__srv__PlaySequence_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
gesture_management__srv__PlaySequence_Request__Sequence__copy(
  const gesture_management__srv__PlaySequence_Request__Sequence * input,
  gesture_management__srv__PlaySequence_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(gesture_management__srv__PlaySequence_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    gesture_management__srv__PlaySequence_Request * data =
      (gesture_management__srv__PlaySequence_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!gesture_management__srv__PlaySequence_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          gesture_management__srv__PlaySequence_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!gesture_management__srv__PlaySequence_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `message`
// already included above
// #include "rosidl_runtime_c/string_functions.h"

bool
gesture_management__srv__PlaySequence_Response__init(gesture_management__srv__PlaySequence_Response * msg)
{
  if (!msg) {
    return false;
  }
  // success
  // message
  if (!rosidl_runtime_c__String__init(&msg->message)) {
    gesture_management__srv__PlaySequence_Response__fini(msg);
    return false;
  }
  return true;
}

void
gesture_management__srv__PlaySequence_Response__fini(gesture_management__srv__PlaySequence_Response * msg)
{
  if (!msg) {
    return;
  }
  // success
  // message
  rosidl_runtime_c__String__fini(&msg->message);
}

bool
gesture_management__srv__PlaySequence_Response__are_equal(const gesture_management__srv__PlaySequence_Response * lhs, const gesture_management__srv__PlaySequence_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // success
  if (lhs->success != rhs->success) {
    return false;
  }
  // message
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->message), &(rhs->message)))
  {
    return false;
  }
  return true;
}

bool
gesture_management__srv__PlaySequence_Response__copy(
  const gesture_management__srv__PlaySequence_Response * input,
  gesture_management__srv__PlaySequence_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // success
  output->success = input->success;
  // message
  if (!rosidl_runtime_c__String__copy(
      &(input->message), &(output->message)))
  {
    return false;
  }
  return true;
}

gesture_management__srv__PlaySequence_Response *
gesture_management__srv__PlaySequence_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  gesture_management__srv__PlaySequence_Response * msg = (gesture_management__srv__PlaySequence_Response *)allocator.allocate(sizeof(gesture_management__srv__PlaySequence_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(gesture_management__srv__PlaySequence_Response));
  bool success = gesture_management__srv__PlaySequence_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
gesture_management__srv__PlaySequence_Response__destroy(gesture_management__srv__PlaySequence_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    gesture_management__srv__PlaySequence_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
gesture_management__srv__PlaySequence_Response__Sequence__init(gesture_management__srv__PlaySequence_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  gesture_management__srv__PlaySequence_Response * data = NULL;

  if (size) {
    data = (gesture_management__srv__PlaySequence_Response *)allocator.zero_allocate(size, sizeof(gesture_management__srv__PlaySequence_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = gesture_management__srv__PlaySequence_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        gesture_management__srv__PlaySequence_Response__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
gesture_management__srv__PlaySequence_Response__Sequence__fini(gesture_management__srv__PlaySequence_Response__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      gesture_management__srv__PlaySequence_Response__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

gesture_management__srv__PlaySequence_Response__Sequence *
gesture_management__srv__PlaySequence_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  gesture_management__srv__PlaySequence_Response__Sequence * array = (gesture_management__srv__PlaySequence_Response__Sequence *)allocator.allocate(sizeof(gesture_management__srv__PlaySequence_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = gesture_management__srv__PlaySequence_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
gesture_management__srv__PlaySequence_Response__Sequence__destroy(gesture_management__srv__PlaySequence_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    gesture_management__srv__PlaySequence_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
gesture_management__srv__PlaySequence_Response__Sequence__are_equal(const gesture_management__srv__PlaySequence_Response__Sequence * lhs, const gesture_management__srv__PlaySequence_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!gesture_management__srv__PlaySequence_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
gesture_management__srv__PlaySequence_Response__Sequence__copy(
  const gesture_management__srv__PlaySequence_Response__Sequence * input,
  gesture_management__srv__PlaySequence_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(gesture_management__srv__PlaySequence_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    gesture_management__srv__PlaySequence_Response * data =
      (gesture_management__srv__PlaySequence_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!gesture_management__srv__PlaySequence_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          gesture_management__srv__PlaySequence_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!gesture_management__srv__PlaySequence_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
