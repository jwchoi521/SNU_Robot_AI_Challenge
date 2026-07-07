// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from robot_object_detector_ros:msg/FruitClassificationArray.idl
// generated code does not contain a copyright notice
#include "robot_object_detector_ros/msg/detail/fruit_classification_array__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `classifications`
#include "robot_object_detector_ros/msg/detail/fruit_classification__functions.h"

bool
robot_object_detector_ros__msg__FruitClassificationArray__init(robot_object_detector_ros__msg__FruitClassificationArray * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    robot_object_detector_ros__msg__FruitClassificationArray__fini(msg);
    return false;
  }
  // classifications
  if (!robot_object_detector_ros__msg__FruitClassification__Sequence__init(&msg->classifications, 0)) {
    robot_object_detector_ros__msg__FruitClassificationArray__fini(msg);
    return false;
  }
  return true;
}

void
robot_object_detector_ros__msg__FruitClassificationArray__fini(robot_object_detector_ros__msg__FruitClassificationArray * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // classifications
  robot_object_detector_ros__msg__FruitClassification__Sequence__fini(&msg->classifications);
}

bool
robot_object_detector_ros__msg__FruitClassificationArray__are_equal(const robot_object_detector_ros__msg__FruitClassificationArray * lhs, const robot_object_detector_ros__msg__FruitClassificationArray * rhs)
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
  // classifications
  if (!robot_object_detector_ros__msg__FruitClassification__Sequence__are_equal(
      &(lhs->classifications), &(rhs->classifications)))
  {
    return false;
  }
  return true;
}

bool
robot_object_detector_ros__msg__FruitClassificationArray__copy(
  const robot_object_detector_ros__msg__FruitClassificationArray * input,
  robot_object_detector_ros__msg__FruitClassificationArray * output)
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
  // classifications
  if (!robot_object_detector_ros__msg__FruitClassification__Sequence__copy(
      &(input->classifications), &(output->classifications)))
  {
    return false;
  }
  return true;
}

robot_object_detector_ros__msg__FruitClassificationArray *
robot_object_detector_ros__msg__FruitClassificationArray__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_object_detector_ros__msg__FruitClassificationArray * msg = (robot_object_detector_ros__msg__FruitClassificationArray *)allocator.allocate(sizeof(robot_object_detector_ros__msg__FruitClassificationArray), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(robot_object_detector_ros__msg__FruitClassificationArray));
  bool success = robot_object_detector_ros__msg__FruitClassificationArray__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
robot_object_detector_ros__msg__FruitClassificationArray__destroy(robot_object_detector_ros__msg__FruitClassificationArray * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    robot_object_detector_ros__msg__FruitClassificationArray__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
robot_object_detector_ros__msg__FruitClassificationArray__Sequence__init(robot_object_detector_ros__msg__FruitClassificationArray__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_object_detector_ros__msg__FruitClassificationArray * data = NULL;

  if (size) {
    data = (robot_object_detector_ros__msg__FruitClassificationArray *)allocator.zero_allocate(size, sizeof(robot_object_detector_ros__msg__FruitClassificationArray), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = robot_object_detector_ros__msg__FruitClassificationArray__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        robot_object_detector_ros__msg__FruitClassificationArray__fini(&data[i - 1]);
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
robot_object_detector_ros__msg__FruitClassificationArray__Sequence__fini(robot_object_detector_ros__msg__FruitClassificationArray__Sequence * array)
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
      robot_object_detector_ros__msg__FruitClassificationArray__fini(&array->data[i]);
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

robot_object_detector_ros__msg__FruitClassificationArray__Sequence *
robot_object_detector_ros__msg__FruitClassificationArray__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_object_detector_ros__msg__FruitClassificationArray__Sequence * array = (robot_object_detector_ros__msg__FruitClassificationArray__Sequence *)allocator.allocate(sizeof(robot_object_detector_ros__msg__FruitClassificationArray__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = robot_object_detector_ros__msg__FruitClassificationArray__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
robot_object_detector_ros__msg__FruitClassificationArray__Sequence__destroy(robot_object_detector_ros__msg__FruitClassificationArray__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    robot_object_detector_ros__msg__FruitClassificationArray__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
robot_object_detector_ros__msg__FruitClassificationArray__Sequence__are_equal(const robot_object_detector_ros__msg__FruitClassificationArray__Sequence * lhs, const robot_object_detector_ros__msg__FruitClassificationArray__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!robot_object_detector_ros__msg__FruitClassificationArray__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
robot_object_detector_ros__msg__FruitClassificationArray__Sequence__copy(
  const robot_object_detector_ros__msg__FruitClassificationArray__Sequence * input,
  robot_object_detector_ros__msg__FruitClassificationArray__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(robot_object_detector_ros__msg__FruitClassificationArray);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    robot_object_detector_ros__msg__FruitClassificationArray * data =
      (robot_object_detector_ros__msg__FruitClassificationArray *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!robot_object_detector_ros__msg__FruitClassificationArray__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          robot_object_detector_ros__msg__FruitClassificationArray__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!robot_object_detector_ros__msg__FruitClassificationArray__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
