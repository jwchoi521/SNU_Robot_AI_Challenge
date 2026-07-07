// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from snu_robot_interfaces:msg/GripperState.idl
// generated code does not contain a copyright notice
#include "snu_robot_interfaces/msg/detail/gripper_state__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"

bool
snu_robot_interfaces__msg__GripperState__init(snu_robot_interfaces__msg__GripperState * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    snu_robot_interfaces__msg__GripperState__fini(msg);
    return false;
  }
  // is_open
  // is_closed
  // has_object
  // opening_m
  // effort
  return true;
}

void
snu_robot_interfaces__msg__GripperState__fini(snu_robot_interfaces__msg__GripperState * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // is_open
  // is_closed
  // has_object
  // opening_m
  // effort
}

bool
snu_robot_interfaces__msg__GripperState__are_equal(const snu_robot_interfaces__msg__GripperState * lhs, const snu_robot_interfaces__msg__GripperState * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__are_equal(
      &(lhs->header), &(rhs->header)))
  {
    return false;
  }
  // is_open
  if (lhs->is_open != rhs->is_open) {
    return false;
  }
  // is_closed
  if (lhs->is_closed != rhs->is_closed) {
    return false;
  }
  // has_object
  if (lhs->has_object != rhs->has_object) {
    return false;
  }
  // opening_m
  if (lhs->opening_m != rhs->opening_m) {
    return false;
  }
  // effort
  if (lhs->effort != rhs->effort) {
    return false;
  }
  return true;
}

bool
snu_robot_interfaces__msg__GripperState__copy(
  const snu_robot_interfaces__msg__GripperState * input,
  snu_robot_interfaces__msg__GripperState * output)
{
  if (!input || !output) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__copy(
      &(input->header), &(output->header)))
  {
    return false;
  }
  // is_open
  output->is_open = input->is_open;
  // is_closed
  output->is_closed = input->is_closed;
  // has_object
  output->has_object = input->has_object;
  // opening_m
  output->opening_m = input->opening_m;
  // effort
  output->effort = input->effort;
  return true;
}

snu_robot_interfaces__msg__GripperState *
snu_robot_interfaces__msg__GripperState__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  snu_robot_interfaces__msg__GripperState * msg = (snu_robot_interfaces__msg__GripperState *)allocator.allocate(sizeof(snu_robot_interfaces__msg__GripperState), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(snu_robot_interfaces__msg__GripperState));
  bool success = snu_robot_interfaces__msg__GripperState__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
snu_robot_interfaces__msg__GripperState__destroy(snu_robot_interfaces__msg__GripperState * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    snu_robot_interfaces__msg__GripperState__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
snu_robot_interfaces__msg__GripperState__Sequence__init(snu_robot_interfaces__msg__GripperState__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  snu_robot_interfaces__msg__GripperState * data = NULL;

  if (size) {
    data = (snu_robot_interfaces__msg__GripperState *)allocator.zero_allocate(size, sizeof(snu_robot_interfaces__msg__GripperState), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = snu_robot_interfaces__msg__GripperState__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        snu_robot_interfaces__msg__GripperState__fini(&data[i - 1]);
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
snu_robot_interfaces__msg__GripperState__Sequence__fini(snu_robot_interfaces__msg__GripperState__Sequence * array)
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
      snu_robot_interfaces__msg__GripperState__fini(&array->data[i]);
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

snu_robot_interfaces__msg__GripperState__Sequence *
snu_robot_interfaces__msg__GripperState__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  snu_robot_interfaces__msg__GripperState__Sequence * array = (snu_robot_interfaces__msg__GripperState__Sequence *)allocator.allocate(sizeof(snu_robot_interfaces__msg__GripperState__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = snu_robot_interfaces__msg__GripperState__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
snu_robot_interfaces__msg__GripperState__Sequence__destroy(snu_robot_interfaces__msg__GripperState__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    snu_robot_interfaces__msg__GripperState__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
snu_robot_interfaces__msg__GripperState__Sequence__are_equal(const snu_robot_interfaces__msg__GripperState__Sequence * lhs, const snu_robot_interfaces__msg__GripperState__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!snu_robot_interfaces__msg__GripperState__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
snu_robot_interfaces__msg__GripperState__Sequence__copy(
  const snu_robot_interfaces__msg__GripperState__Sequence * input,
  snu_robot_interfaces__msg__GripperState__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(snu_robot_interfaces__msg__GripperState);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    snu_robot_interfaces__msg__GripperState * data =
      (snu_robot_interfaces__msg__GripperState *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!snu_robot_interfaces__msg__GripperState__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          snu_robot_interfaces__msg__GripperState__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!snu_robot_interfaces__msg__GripperState__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
