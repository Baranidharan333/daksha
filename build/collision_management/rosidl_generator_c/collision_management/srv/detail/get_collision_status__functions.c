// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from collision_management:srv/GetCollisionStatus.idl
// generated code does not contain a copyright notice
#include "collision_management/srv/detail/get_collision_status__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

bool
collision_management__srv__GetCollisionStatus_Request__init(collision_management__srv__GetCollisionStatus_Request * msg)
{
  if (!msg) {
    return false;
  }
  // structure_needs_at_least_one_member
  return true;
}

void
collision_management__srv__GetCollisionStatus_Request__fini(collision_management__srv__GetCollisionStatus_Request * msg)
{
  if (!msg) {
    return;
  }
  // structure_needs_at_least_one_member
}

bool
collision_management__srv__GetCollisionStatus_Request__are_equal(const collision_management__srv__GetCollisionStatus_Request * lhs, const collision_management__srv__GetCollisionStatus_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // structure_needs_at_least_one_member
  if (lhs->structure_needs_at_least_one_member != rhs->structure_needs_at_least_one_member) {
    return false;
  }
  return true;
}

bool
collision_management__srv__GetCollisionStatus_Request__copy(
  const collision_management__srv__GetCollisionStatus_Request * input,
  collision_management__srv__GetCollisionStatus_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // structure_needs_at_least_one_member
  output->structure_needs_at_least_one_member = input->structure_needs_at_least_one_member;
  return true;
}

collision_management__srv__GetCollisionStatus_Request *
collision_management__srv__GetCollisionStatus_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  collision_management__srv__GetCollisionStatus_Request * msg = (collision_management__srv__GetCollisionStatus_Request *)allocator.allocate(sizeof(collision_management__srv__GetCollisionStatus_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(collision_management__srv__GetCollisionStatus_Request));
  bool success = collision_management__srv__GetCollisionStatus_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
collision_management__srv__GetCollisionStatus_Request__destroy(collision_management__srv__GetCollisionStatus_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    collision_management__srv__GetCollisionStatus_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
collision_management__srv__GetCollisionStatus_Request__Sequence__init(collision_management__srv__GetCollisionStatus_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  collision_management__srv__GetCollisionStatus_Request * data = NULL;

  if (size) {
    data = (collision_management__srv__GetCollisionStatus_Request *)allocator.zero_allocate(size, sizeof(collision_management__srv__GetCollisionStatus_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = collision_management__srv__GetCollisionStatus_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        collision_management__srv__GetCollisionStatus_Request__fini(&data[i - 1]);
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
collision_management__srv__GetCollisionStatus_Request__Sequence__fini(collision_management__srv__GetCollisionStatus_Request__Sequence * array)
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
      collision_management__srv__GetCollisionStatus_Request__fini(&array->data[i]);
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

collision_management__srv__GetCollisionStatus_Request__Sequence *
collision_management__srv__GetCollisionStatus_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  collision_management__srv__GetCollisionStatus_Request__Sequence * array = (collision_management__srv__GetCollisionStatus_Request__Sequence *)allocator.allocate(sizeof(collision_management__srv__GetCollisionStatus_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = collision_management__srv__GetCollisionStatus_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
collision_management__srv__GetCollisionStatus_Request__Sequence__destroy(collision_management__srv__GetCollisionStatus_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    collision_management__srv__GetCollisionStatus_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
collision_management__srv__GetCollisionStatus_Request__Sequence__are_equal(const collision_management__srv__GetCollisionStatus_Request__Sequence * lhs, const collision_management__srv__GetCollisionStatus_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!collision_management__srv__GetCollisionStatus_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
collision_management__srv__GetCollisionStatus_Request__Sequence__copy(
  const collision_management__srv__GetCollisionStatus_Request__Sequence * input,
  collision_management__srv__GetCollisionStatus_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(collision_management__srv__GetCollisionStatus_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    collision_management__srv__GetCollisionStatus_Request * data =
      (collision_management__srv__GetCollisionStatus_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!collision_management__srv__GetCollisionStatus_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          collision_management__srv__GetCollisionStatus_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!collision_management__srv__GetCollisionStatus_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `status`
#include "sensor_msgs/msg/detail/joint_state__functions.h"

bool
collision_management__srv__GetCollisionStatus_Response__init(collision_management__srv__GetCollisionStatus_Response * msg)
{
  if (!msg) {
    return false;
  }
  // in_collision
  // status
  if (!sensor_msgs__msg__JointState__init(&msg->status)) {
    collision_management__srv__GetCollisionStatus_Response__fini(msg);
    return false;
  }
  return true;
}

void
collision_management__srv__GetCollisionStatus_Response__fini(collision_management__srv__GetCollisionStatus_Response * msg)
{
  if (!msg) {
    return;
  }
  // in_collision
  // status
  sensor_msgs__msg__JointState__fini(&msg->status);
}

bool
collision_management__srv__GetCollisionStatus_Response__are_equal(const collision_management__srv__GetCollisionStatus_Response * lhs, const collision_management__srv__GetCollisionStatus_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // in_collision
  if (lhs->in_collision != rhs->in_collision) {
    return false;
  }
  // status
  if (!sensor_msgs__msg__JointState__are_equal(
      &(lhs->status), &(rhs->status)))
  {
    return false;
  }
  return true;
}

bool
collision_management__srv__GetCollisionStatus_Response__copy(
  const collision_management__srv__GetCollisionStatus_Response * input,
  collision_management__srv__GetCollisionStatus_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // in_collision
  output->in_collision = input->in_collision;
  // status
  if (!sensor_msgs__msg__JointState__copy(
      &(input->status), &(output->status)))
  {
    return false;
  }
  return true;
}

collision_management__srv__GetCollisionStatus_Response *
collision_management__srv__GetCollisionStatus_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  collision_management__srv__GetCollisionStatus_Response * msg = (collision_management__srv__GetCollisionStatus_Response *)allocator.allocate(sizeof(collision_management__srv__GetCollisionStatus_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(collision_management__srv__GetCollisionStatus_Response));
  bool success = collision_management__srv__GetCollisionStatus_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
collision_management__srv__GetCollisionStatus_Response__destroy(collision_management__srv__GetCollisionStatus_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    collision_management__srv__GetCollisionStatus_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
collision_management__srv__GetCollisionStatus_Response__Sequence__init(collision_management__srv__GetCollisionStatus_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  collision_management__srv__GetCollisionStatus_Response * data = NULL;

  if (size) {
    data = (collision_management__srv__GetCollisionStatus_Response *)allocator.zero_allocate(size, sizeof(collision_management__srv__GetCollisionStatus_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = collision_management__srv__GetCollisionStatus_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        collision_management__srv__GetCollisionStatus_Response__fini(&data[i - 1]);
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
collision_management__srv__GetCollisionStatus_Response__Sequence__fini(collision_management__srv__GetCollisionStatus_Response__Sequence * array)
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
      collision_management__srv__GetCollisionStatus_Response__fini(&array->data[i]);
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

collision_management__srv__GetCollisionStatus_Response__Sequence *
collision_management__srv__GetCollisionStatus_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  collision_management__srv__GetCollisionStatus_Response__Sequence * array = (collision_management__srv__GetCollisionStatus_Response__Sequence *)allocator.allocate(sizeof(collision_management__srv__GetCollisionStatus_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = collision_management__srv__GetCollisionStatus_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
collision_management__srv__GetCollisionStatus_Response__Sequence__destroy(collision_management__srv__GetCollisionStatus_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    collision_management__srv__GetCollisionStatus_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
collision_management__srv__GetCollisionStatus_Response__Sequence__are_equal(const collision_management__srv__GetCollisionStatus_Response__Sequence * lhs, const collision_management__srv__GetCollisionStatus_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!collision_management__srv__GetCollisionStatus_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
collision_management__srv__GetCollisionStatus_Response__Sequence__copy(
  const collision_management__srv__GetCollisionStatus_Response__Sequence * input,
  collision_management__srv__GetCollisionStatus_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(collision_management__srv__GetCollisionStatus_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    collision_management__srv__GetCollisionStatus_Response * data =
      (collision_management__srv__GetCollisionStatus_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!collision_management__srv__GetCollisionStatus_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          collision_management__srv__GetCollisionStatus_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!collision_management__srv__GetCollisionStatus_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
