// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from snu_robot_interfaces:msg/PerceivedObjectArray.idl
// generated code does not contain a copyright notice
#include "snu_robot_interfaces/msg/detail/perceived_object_array__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `objects`
#include "snu_robot_interfaces/msg/detail/perceived_object__functions.h"

bool
snu_robot_interfaces__msg__PerceivedObjectArray__init(snu_robot_interfaces__msg__PerceivedObjectArray * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    snu_robot_interfaces__msg__PerceivedObjectArray__fini(msg);
    return false;
  }
  // objects
  if (!snu_robot_interfaces__msg__PerceivedObject__Sequence__init(&msg->objects, 0)) {
    snu_robot_interfaces__msg__PerceivedObjectArray__fini(msg);
    return false;
  }
  return true;
}

void
snu_robot_interfaces__msg__PerceivedObjectArray__fini(snu_robot_interfaces__msg__PerceivedObjectArray * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // objects
  snu_robot_interfaces__msg__PerceivedObject__Sequence__fini(&msg->objects);
}

bool
snu_robot_interfaces__msg__PerceivedObjectArray__are_equal(const snu_robot_interfaces__msg__PerceivedObjectArray * lhs, const snu_robot_interfaces__msg__PerceivedObjectArray * rhs)
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
  // objects
  if (!snu_robot_interfaces__msg__PerceivedObject__Sequence__are_equal(
      &(lhs->objects), &(rhs->objects)))
  {
    return false;
  }
  return true;
}

bool
snu_robot_interfaces__msg__PerceivedObjectArray__copy(
  const snu_robot_interfaces__msg__PerceivedObjectArray * input,
  snu_robot_interfaces__msg__PerceivedObjectArray * output)
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
  // objects
  if (!snu_robot_interfaces__msg__PerceivedObject__Sequence__copy(
      &(input->objects), &(output->objects)))
  {
    return false;
  }
  return true;
}

snu_robot_interfaces__msg__PerceivedObjectArray *
snu_robot_interfaces__msg__PerceivedObjectArray__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  snu_robot_interfaces__msg__PerceivedObjectArray * msg = (snu_robot_interfaces__msg__PerceivedObjectArray *)allocator.allocate(sizeof(snu_robot_interfaces__msg__PerceivedObjectArray), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(snu_robot_interfaces__msg__PerceivedObjectArray));
  bool success = snu_robot_interfaces__msg__PerceivedObjectArray__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
snu_robot_interfaces__msg__PerceivedObjectArray__destroy(snu_robot_interfaces__msg__PerceivedObjectArray * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    snu_robot_interfaces__msg__PerceivedObjectArray__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
snu_robot_interfaces__msg__PerceivedObjectArray__Sequence__init(snu_robot_interfaces__msg__PerceivedObjectArray__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  snu_robot_interfaces__msg__PerceivedObjectArray * data = NULL;

  if (size) {
    data = (snu_robot_interfaces__msg__PerceivedObjectArray *)allocator.zero_allocate(size, sizeof(snu_robot_interfaces__msg__PerceivedObjectArray), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = snu_robot_interfaces__msg__PerceivedObjectArray__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        snu_robot_interfaces__msg__PerceivedObjectArray__fini(&data[i - 1]);
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
snu_robot_interfaces__msg__PerceivedObjectArray__Sequence__fini(snu_robot_interfaces__msg__PerceivedObjectArray__Sequence * array)
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
      snu_robot_interfaces__msg__PerceivedObjectArray__fini(&array->data[i]);
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

snu_robot_interfaces__msg__PerceivedObjectArray__Sequence *
snu_robot_interfaces__msg__PerceivedObjectArray__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  snu_robot_interfaces__msg__PerceivedObjectArray__Sequence * array = (snu_robot_interfaces__msg__PerceivedObjectArray__Sequence *)allocator.allocate(sizeof(snu_robot_interfaces__msg__PerceivedObjectArray__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = snu_robot_interfaces__msg__PerceivedObjectArray__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
snu_robot_interfaces__msg__PerceivedObjectArray__Sequence__destroy(snu_robot_interfaces__msg__PerceivedObjectArray__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    snu_robot_interfaces__msg__PerceivedObjectArray__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
snu_robot_interfaces__msg__PerceivedObjectArray__Sequence__are_equal(const snu_robot_interfaces__msg__PerceivedObjectArray__Sequence * lhs, const snu_robot_interfaces__msg__PerceivedObjectArray__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!snu_robot_interfaces__msg__PerceivedObjectArray__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
snu_robot_interfaces__msg__PerceivedObjectArray__Sequence__copy(
  const snu_robot_interfaces__msg__PerceivedObjectArray__Sequence * input,
  snu_robot_interfaces__msg__PerceivedObjectArray__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(snu_robot_interfaces__msg__PerceivedObjectArray);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    snu_robot_interfaces__msg__PerceivedObjectArray * data =
      (snu_robot_interfaces__msg__PerceivedObjectArray *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!snu_robot_interfaces__msg__PerceivedObjectArray__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          snu_robot_interfaces__msg__PerceivedObjectArray__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!snu_robot_interfaces__msg__PerceivedObjectArray__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
