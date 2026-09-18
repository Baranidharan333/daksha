// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from daksha_msgs:srv/StartRecord.idl
// generated code does not contain a copyright notice
#include "daksha_msgs/srv/detail/start_record__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

// Include directives for member types
// Member `dataset_name`
#include "rosidl_runtime_c/string_functions.h"

bool
daksha_msgs__srv__StartRecord_Request__init(daksha_msgs__srv__StartRecord_Request * msg)
{
  if (!msg) {
    return false;
  }
  // dataset_name
  if (!rosidl_runtime_c__String__init(&msg->dataset_name)) {
    daksha_msgs__srv__StartRecord_Request__fini(msg);
    return false;
  }
  // episode_length
  // record_hz
  // max_episodes
  return true;
}

void
daksha_msgs__srv__StartRecord_Request__fini(daksha_msgs__srv__StartRecord_Request * msg)
{
  if (!msg) {
    return;
  }
  // dataset_name
  rosidl_runtime_c__String__fini(&msg->dataset_name);
  // episode_length
  // record_hz
  // max_episodes
}

bool
daksha_msgs__srv__StartRecord_Request__are_equal(const daksha_msgs__srv__StartRecord_Request * lhs, const daksha_msgs__srv__StartRecord_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // dataset_name
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->dataset_name), &(rhs->dataset_name)))
  {
    return false;
  }
  // episode_length
  if (lhs->episode_length != rhs->episode_length) {
    return false;
  }
  // record_hz
  if (lhs->record_hz != rhs->record_hz) {
    return false;
  }
  // max_episodes
  if (lhs->max_episodes != rhs->max_episodes) {
    return false;
  }
  return true;
}

bool
daksha_msgs__srv__StartRecord_Request__copy(
  const daksha_msgs__srv__StartRecord_Request * input,
  daksha_msgs__srv__StartRecord_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // dataset_name
  if (!rosidl_runtime_c__String__copy(
      &(input->dataset_name), &(output->dataset_name)))
  {
    return false;
  }
  // episode_length
  output->episode_length = input->episode_length;
  // record_hz
  output->record_hz = input->record_hz;
  // max_episodes
  output->max_episodes = input->max_episodes;
  return true;
}

daksha_msgs__srv__StartRecord_Request *
daksha_msgs__srv__StartRecord_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  daksha_msgs__srv__StartRecord_Request * msg = (daksha_msgs__srv__StartRecord_Request *)allocator.allocate(sizeof(daksha_msgs__srv__StartRecord_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(daksha_msgs__srv__StartRecord_Request));
  bool success = daksha_msgs__srv__StartRecord_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
daksha_msgs__srv__StartRecord_Request__destroy(daksha_msgs__srv__StartRecord_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    daksha_msgs__srv__StartRecord_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
daksha_msgs__srv__StartRecord_Request__Sequence__init(daksha_msgs__srv__StartRecord_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  daksha_msgs__srv__StartRecord_Request * data = NULL;

  if (size) {
    data = (daksha_msgs__srv__StartRecord_Request *)allocator.zero_allocate(size, sizeof(daksha_msgs__srv__StartRecord_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = daksha_msgs__srv__StartRecord_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        daksha_msgs__srv__StartRecord_Request__fini(&data[i - 1]);
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
daksha_msgs__srv__StartRecord_Request__Sequence__fini(daksha_msgs__srv__StartRecord_Request__Sequence * array)
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
      daksha_msgs__srv__StartRecord_Request__fini(&array->data[i]);
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

daksha_msgs__srv__StartRecord_Request__Sequence *
daksha_msgs__srv__StartRecord_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  daksha_msgs__srv__StartRecord_Request__Sequence * array = (daksha_msgs__srv__StartRecord_Request__Sequence *)allocator.allocate(sizeof(daksha_msgs__srv__StartRecord_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = daksha_msgs__srv__StartRecord_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
daksha_msgs__srv__StartRecord_Request__Sequence__destroy(daksha_msgs__srv__StartRecord_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    daksha_msgs__srv__StartRecord_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
daksha_msgs__srv__StartRecord_Request__Sequence__are_equal(const daksha_msgs__srv__StartRecord_Request__Sequence * lhs, const daksha_msgs__srv__StartRecord_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!daksha_msgs__srv__StartRecord_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
daksha_msgs__srv__StartRecord_Request__Sequence__copy(
  const daksha_msgs__srv__StartRecord_Request__Sequence * input,
  daksha_msgs__srv__StartRecord_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(daksha_msgs__srv__StartRecord_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    daksha_msgs__srv__StartRecord_Request * data =
      (daksha_msgs__srv__StartRecord_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!daksha_msgs__srv__StartRecord_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          daksha_msgs__srv__StartRecord_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!daksha_msgs__srv__StartRecord_Request__copy(
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
daksha_msgs__srv__StartRecord_Response__init(daksha_msgs__srv__StartRecord_Response * msg)
{
  if (!msg) {
    return false;
  }
  // success
  // message
  if (!rosidl_runtime_c__String__init(&msg->message)) {
    daksha_msgs__srv__StartRecord_Response__fini(msg);
    return false;
  }
  return true;
}

void
daksha_msgs__srv__StartRecord_Response__fini(daksha_msgs__srv__StartRecord_Response * msg)
{
  if (!msg) {
    return;
  }
  // success
  // message
  rosidl_runtime_c__String__fini(&msg->message);
}

bool
daksha_msgs__srv__StartRecord_Response__are_equal(const daksha_msgs__srv__StartRecord_Response * lhs, const daksha_msgs__srv__StartRecord_Response * rhs)
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
daksha_msgs__srv__StartRecord_Response__copy(
  const daksha_msgs__srv__StartRecord_Response * input,
  daksha_msgs__srv__StartRecord_Response * output)
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

daksha_msgs__srv__StartRecord_Response *
daksha_msgs__srv__StartRecord_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  daksha_msgs__srv__StartRecord_Response * msg = (daksha_msgs__srv__StartRecord_Response *)allocator.allocate(sizeof(daksha_msgs__srv__StartRecord_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(daksha_msgs__srv__StartRecord_Response));
  bool success = daksha_msgs__srv__StartRecord_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
daksha_msgs__srv__StartRecord_Response__destroy(daksha_msgs__srv__StartRecord_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    daksha_msgs__srv__StartRecord_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
daksha_msgs__srv__StartRecord_Response__Sequence__init(daksha_msgs__srv__StartRecord_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  daksha_msgs__srv__StartRecord_Response * data = NULL;

  if (size) {
    data = (daksha_msgs__srv__StartRecord_Response *)allocator.zero_allocate(size, sizeof(daksha_msgs__srv__StartRecord_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = daksha_msgs__srv__StartRecord_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        daksha_msgs__srv__StartRecord_Response__fini(&data[i - 1]);
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
daksha_msgs__srv__StartRecord_Response__Sequence__fini(daksha_msgs__srv__StartRecord_Response__Sequence * array)
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
      daksha_msgs__srv__StartRecord_Response__fini(&array->data[i]);
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

daksha_msgs__srv__StartRecord_Response__Sequence *
daksha_msgs__srv__StartRecord_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  daksha_msgs__srv__StartRecord_Response__Sequence * array = (daksha_msgs__srv__StartRecord_Response__Sequence *)allocator.allocate(sizeof(daksha_msgs__srv__StartRecord_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = daksha_msgs__srv__StartRecord_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
daksha_msgs__srv__StartRecord_Response__Sequence__destroy(daksha_msgs__srv__StartRecord_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    daksha_msgs__srv__StartRecord_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
daksha_msgs__srv__StartRecord_Response__Sequence__are_equal(const daksha_msgs__srv__StartRecord_Response__Sequence * lhs, const daksha_msgs__srv__StartRecord_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!daksha_msgs__srv__StartRecord_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
daksha_msgs__srv__StartRecord_Response__Sequence__copy(
  const daksha_msgs__srv__StartRecord_Response__Sequence * input,
  daksha_msgs__srv__StartRecord_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(daksha_msgs__srv__StartRecord_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    daksha_msgs__srv__StartRecord_Response * data =
      (daksha_msgs__srv__StartRecord_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!daksha_msgs__srv__StartRecord_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          daksha_msgs__srv__StartRecord_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!daksha_msgs__srv__StartRecord_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
