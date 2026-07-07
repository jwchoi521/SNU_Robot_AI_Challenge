// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from robot_object_detector_ros:msg/Detection2D.idl
// generated code does not contain a copyright notice
#include "robot_object_detector_ros/msg/detail/detection2_d__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `class_name`
#include "rosidl_runtime_c/string_functions.h"

bool
robot_object_detector_ros__msg__Detection2D__init(robot_object_detector_ros__msg__Detection2D * msg)
{
  if (!msg) {
    return false;
  }
  // class_id
  // class_name
  if (!rosidl_runtime_c__String__init(&msg->class_name)) {
    robot_object_detector_ros__msg__Detection2D__fini(msg);
    return false;
  }
  // confidence
  // x1
  // y1
  // x2
  // y2
  return true;
}

void
robot_object_detector_ros__msg__Detection2D__fini(robot_object_detector_ros__msg__Detection2D * msg)
{
  if (!msg) {
    return;
  }
  // class_id
  // class_name
  rosidl_runtime_c__String__fini(&msg->class_name);
  // confidence
  // x1
  // y1
  // x2
  // y2
}

bool
robot_object_detector_ros__msg__Detection2D__are_equal(const robot_object_detector_ros__msg__Detection2D * lhs, const robot_object_detector_ros__msg__Detection2D * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // class_id
  if (lhs->class_id != rhs->class_id) {
    return false;
  }
  // class_name
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->class_name), &(rhs->class_name)))
  {
    return false;
  }
  // confidence
  if (lhs->confidence != rhs->confidence) {
    return false;
  }
  // x1
  if (lhs->x1 != rhs->x1) {
    return false;
  }
  // y1
  if (lhs->y1 != rhs->y1) {
    return false;
  }
  // x2
  if (lhs->x2 != rhs->x2) {
    return false;
  }
  // y2
  if (lhs->y2 != rhs->y2) {
    return false;
  }
  return true;
}

bool
robot_object_detector_ros__msg__Detection2D__copy(
  const robot_object_detector_ros__msg__Detection2D * input,
  robot_object_detector_ros__msg__Detection2D * output)
{
  if (!input || !output) {
    return false;
  }
  // class_id
  output->class_id = input->class_id;
  // class_name
  if (!rosidl_runtime_c__String__copy(
      &(input->class_name), &(output->class_name)))
  {
    return false;
  }
  // confidence
  output->confidence = input->confidence;
  // x1
  output->x1 = input->x1;
  // y1
  output->y1 = input->y1;
  // x2
  output->x2 = input->x2;
  // y2
  output->y2 = input->y2;
  return true;
}

robot_object_detector_ros__msg__Detection2D *
robot_object_detector_ros__msg__Detection2D__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_object_detector_ros__msg__Detection2D * msg = (robot_object_detector_ros__msg__Detection2D *)allocator.allocate(sizeof(robot_object_detector_ros__msg__Detection2D), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(robot_object_detector_ros__msg__Detection2D));
  bool success = robot_object_detector_ros__msg__Detection2D__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
robot_object_detector_ros__msg__Detection2D__destroy(robot_object_detector_ros__msg__Detection2D * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    robot_object_detector_ros__msg__Detection2D__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
robot_object_detector_ros__msg__Detection2D__Sequence__init(robot_object_detector_ros__msg__Detection2D__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_object_detector_ros__msg__Detection2D * data = NULL;

  if (size) {
    data = (robot_object_detector_ros__msg__Detection2D *)allocator.zero_allocate(size, sizeof(robot_object_detector_ros__msg__Detection2D), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = robot_object_detector_ros__msg__Detection2D__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        robot_object_detector_ros__msg__Detection2D__fini(&data[i - 1]);
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
robot_object_detector_ros__msg__Detection2D__Sequence__fini(robot_object_detector_ros__msg__Detection2D__Sequence * array)
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
      robot_object_detector_ros__msg__Detection2D__fini(&array->data[i]);
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

robot_object_detector_ros__msg__Detection2D__Sequence *
robot_object_detector_ros__msg__Detection2D__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_object_detector_ros__msg__Detection2D__Sequence * array = (robot_object_detector_ros__msg__Detection2D__Sequence *)allocator.allocate(sizeof(robot_object_detector_ros__msg__Detection2D__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = robot_object_detector_ros__msg__Detection2D__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
robot_object_detector_ros__msg__Detection2D__Sequence__destroy(robot_object_detector_ros__msg__Detection2D__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    robot_object_detector_ros__msg__Detection2D__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
robot_object_detector_ros__msg__Detection2D__Sequence__are_equal(const robot_object_detector_ros__msg__Detection2D__Sequence * lhs, const robot_object_detector_ros__msg__Detection2D__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!robot_object_detector_ros__msg__Detection2D__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
robot_object_detector_ros__msg__Detection2D__Sequence__copy(
  const robot_object_detector_ros__msg__Detection2D__Sequence * input,
  robot_object_detector_ros__msg__Detection2D__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(robot_object_detector_ros__msg__Detection2D);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    robot_object_detector_ros__msg__Detection2D * data =
      (robot_object_detector_ros__msg__Detection2D *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!robot_object_detector_ros__msg__Detection2D__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          robot_object_detector_ros__msg__Detection2D__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!robot_object_detector_ros__msg__Detection2D__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
