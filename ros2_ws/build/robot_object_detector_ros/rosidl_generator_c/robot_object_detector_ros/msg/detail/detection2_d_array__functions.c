// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from robot_object_detector_ros:msg/Detection2DArray.idl
// generated code does not contain a copyright notice
#include "robot_object_detector_ros/msg/detail/detection2_d_array__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `detections`
#include "robot_object_detector_ros/msg/detail/detection2_d__functions.h"

bool
robot_object_detector_ros__msg__Detection2DArray__init(robot_object_detector_ros__msg__Detection2DArray * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    robot_object_detector_ros__msg__Detection2DArray__fini(msg);
    return false;
  }
  // detections
  if (!robot_object_detector_ros__msg__Detection2D__Sequence__init(&msg->detections, 0)) {
    robot_object_detector_ros__msg__Detection2DArray__fini(msg);
    return false;
  }
  return true;
}

void
robot_object_detector_ros__msg__Detection2DArray__fini(robot_object_detector_ros__msg__Detection2DArray * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // detections
  robot_object_detector_ros__msg__Detection2D__Sequence__fini(&msg->detections);
}

bool
robot_object_detector_ros__msg__Detection2DArray__are_equal(const robot_object_detector_ros__msg__Detection2DArray * lhs, const robot_object_detector_ros__msg__Detection2DArray * rhs)
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
  // detections
  if (!robot_object_detector_ros__msg__Detection2D__Sequence__are_equal(
      &(lhs->detections), &(rhs->detections)))
  {
    return false;
  }
  return true;
}

bool
robot_object_detector_ros__msg__Detection2DArray__copy(
  const robot_object_detector_ros__msg__Detection2DArray * input,
  robot_object_detector_ros__msg__Detection2DArray * output)
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
  // detections
  if (!robot_object_detector_ros__msg__Detection2D__Sequence__copy(
      &(input->detections), &(output->detections)))
  {
    return false;
  }
  return true;
}

robot_object_detector_ros__msg__Detection2DArray *
robot_object_detector_ros__msg__Detection2DArray__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_object_detector_ros__msg__Detection2DArray * msg = (robot_object_detector_ros__msg__Detection2DArray *)allocator.allocate(sizeof(robot_object_detector_ros__msg__Detection2DArray), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(robot_object_detector_ros__msg__Detection2DArray));
  bool success = robot_object_detector_ros__msg__Detection2DArray__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
robot_object_detector_ros__msg__Detection2DArray__destroy(robot_object_detector_ros__msg__Detection2DArray * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    robot_object_detector_ros__msg__Detection2DArray__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
robot_object_detector_ros__msg__Detection2DArray__Sequence__init(robot_object_detector_ros__msg__Detection2DArray__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_object_detector_ros__msg__Detection2DArray * data = NULL;

  if (size) {
    data = (robot_object_detector_ros__msg__Detection2DArray *)allocator.zero_allocate(size, sizeof(robot_object_detector_ros__msg__Detection2DArray), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = robot_object_detector_ros__msg__Detection2DArray__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        robot_object_detector_ros__msg__Detection2DArray__fini(&data[i - 1]);
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
robot_object_detector_ros__msg__Detection2DArray__Sequence__fini(robot_object_detector_ros__msg__Detection2DArray__Sequence * array)
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
      robot_object_detector_ros__msg__Detection2DArray__fini(&array->data[i]);
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

robot_object_detector_ros__msg__Detection2DArray__Sequence *
robot_object_detector_ros__msg__Detection2DArray__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_object_detector_ros__msg__Detection2DArray__Sequence * array = (robot_object_detector_ros__msg__Detection2DArray__Sequence *)allocator.allocate(sizeof(robot_object_detector_ros__msg__Detection2DArray__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = robot_object_detector_ros__msg__Detection2DArray__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
robot_object_detector_ros__msg__Detection2DArray__Sequence__destroy(robot_object_detector_ros__msg__Detection2DArray__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    robot_object_detector_ros__msg__Detection2DArray__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
robot_object_detector_ros__msg__Detection2DArray__Sequence__are_equal(const robot_object_detector_ros__msg__Detection2DArray__Sequence * lhs, const robot_object_detector_ros__msg__Detection2DArray__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!robot_object_detector_ros__msg__Detection2DArray__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
robot_object_detector_ros__msg__Detection2DArray__Sequence__copy(
  const robot_object_detector_ros__msg__Detection2DArray__Sequence * input,
  robot_object_detector_ros__msg__Detection2DArray__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(robot_object_detector_ros__msg__Detection2DArray);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    robot_object_detector_ros__msg__Detection2DArray * data =
      (robot_object_detector_ros__msg__Detection2DArray *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!robot_object_detector_ros__msg__Detection2DArray__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          robot_object_detector_ros__msg__Detection2DArray__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!robot_object_detector_ros__msg__Detection2DArray__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
