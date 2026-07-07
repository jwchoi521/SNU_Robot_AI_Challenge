// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from robot_object_detector_ros:msg/FruitClassification.idl
// generated code does not contain a copyright notice
#include "robot_object_detector_ros/msg/detail/fruit_classification__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `cube`
#include "robot_object_detector_ros/msg/detail/detection2_d__functions.h"
// Member `fruit_kind`
// Member `class_names`
#include "rosidl_runtime_c/string_functions.h"
// Member `probabilities`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

bool
robot_object_detector_ros__msg__FruitClassification__init(robot_object_detector_ros__msg__FruitClassification * msg)
{
  if (!msg) {
    return false;
  }
  // cube
  if (!robot_object_detector_ros__msg__Detection2D__init(&msg->cube)) {
    robot_object_detector_ros__msg__FruitClassification__fini(msg);
    return false;
  }
  // fruit_kind
  if (!rosidl_runtime_c__String__init(&msg->fruit_kind)) {
    robot_object_detector_ros__msg__FruitClassification__fini(msg);
    return false;
  }
  // confidence
  // pick_allowed
  // class_names
  if (!rosidl_runtime_c__String__Sequence__init(&msg->class_names, 0)) {
    robot_object_detector_ros__msg__FruitClassification__fini(msg);
    return false;
  }
  // probabilities
  if (!rosidl_runtime_c__float__Sequence__init(&msg->probabilities, 0)) {
    robot_object_detector_ros__msg__FruitClassification__fini(msg);
    return false;
  }
  return true;
}

void
robot_object_detector_ros__msg__FruitClassification__fini(robot_object_detector_ros__msg__FruitClassification * msg)
{
  if (!msg) {
    return;
  }
  // cube
  robot_object_detector_ros__msg__Detection2D__fini(&msg->cube);
  // fruit_kind
  rosidl_runtime_c__String__fini(&msg->fruit_kind);
  // confidence
  // pick_allowed
  // class_names
  rosidl_runtime_c__String__Sequence__fini(&msg->class_names);
  // probabilities
  rosidl_runtime_c__float__Sequence__fini(&msg->probabilities);
}

bool
robot_object_detector_ros__msg__FruitClassification__are_equal(const robot_object_detector_ros__msg__FruitClassification * lhs, const robot_object_detector_ros__msg__FruitClassification * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // cube
  if (!robot_object_detector_ros__msg__Detection2D__are_equal(
      &(lhs->cube), &(rhs->cube)))
  {
    return false;
  }
  // fruit_kind
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->fruit_kind), &(rhs->fruit_kind)))
  {
    return false;
  }
  // confidence
  if (lhs->confidence != rhs->confidence) {
    return false;
  }
  // pick_allowed
  if (lhs->pick_allowed != rhs->pick_allowed) {
    return false;
  }
  // class_names
  if (!rosidl_runtime_c__String__Sequence__are_equal(
      &(lhs->class_names), &(rhs->class_names)))
  {
    return false;
  }
  // probabilities
  if (!rosidl_runtime_c__float__Sequence__are_equal(
      &(lhs->probabilities), &(rhs->probabilities)))
  {
    return false;
  }
  return true;
}

bool
robot_object_detector_ros__msg__FruitClassification__copy(
  const robot_object_detector_ros__msg__FruitClassification * input,
  robot_object_detector_ros__msg__FruitClassification * output)
{
  if (!input || !output) {
    return false;
  }
  // cube
  if (!robot_object_detector_ros__msg__Detection2D__copy(
      &(input->cube), &(output->cube)))
  {
    return false;
  }
  // fruit_kind
  if (!rosidl_runtime_c__String__copy(
      &(input->fruit_kind), &(output->fruit_kind)))
  {
    return false;
  }
  // confidence
  output->confidence = input->confidence;
  // pick_allowed
  output->pick_allowed = input->pick_allowed;
  // class_names
  if (!rosidl_runtime_c__String__Sequence__copy(
      &(input->class_names), &(output->class_names)))
  {
    return false;
  }
  // probabilities
  if (!rosidl_runtime_c__float__Sequence__copy(
      &(input->probabilities), &(output->probabilities)))
  {
    return false;
  }
  return true;
}

robot_object_detector_ros__msg__FruitClassification *
robot_object_detector_ros__msg__FruitClassification__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_object_detector_ros__msg__FruitClassification * msg = (robot_object_detector_ros__msg__FruitClassification *)allocator.allocate(sizeof(robot_object_detector_ros__msg__FruitClassification), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(robot_object_detector_ros__msg__FruitClassification));
  bool success = robot_object_detector_ros__msg__FruitClassification__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
robot_object_detector_ros__msg__FruitClassification__destroy(robot_object_detector_ros__msg__FruitClassification * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    robot_object_detector_ros__msg__FruitClassification__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
robot_object_detector_ros__msg__FruitClassification__Sequence__init(robot_object_detector_ros__msg__FruitClassification__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_object_detector_ros__msg__FruitClassification * data = NULL;

  if (size) {
    data = (robot_object_detector_ros__msg__FruitClassification *)allocator.zero_allocate(size, sizeof(robot_object_detector_ros__msg__FruitClassification), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = robot_object_detector_ros__msg__FruitClassification__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        robot_object_detector_ros__msg__FruitClassification__fini(&data[i - 1]);
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
robot_object_detector_ros__msg__FruitClassification__Sequence__fini(robot_object_detector_ros__msg__FruitClassification__Sequence * array)
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
      robot_object_detector_ros__msg__FruitClassification__fini(&array->data[i]);
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

robot_object_detector_ros__msg__FruitClassification__Sequence *
robot_object_detector_ros__msg__FruitClassification__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_object_detector_ros__msg__FruitClassification__Sequence * array = (robot_object_detector_ros__msg__FruitClassification__Sequence *)allocator.allocate(sizeof(robot_object_detector_ros__msg__FruitClassification__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = robot_object_detector_ros__msg__FruitClassification__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
robot_object_detector_ros__msg__FruitClassification__Sequence__destroy(robot_object_detector_ros__msg__FruitClassification__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    robot_object_detector_ros__msg__FruitClassification__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
robot_object_detector_ros__msg__FruitClassification__Sequence__are_equal(const robot_object_detector_ros__msg__FruitClassification__Sequence * lhs, const robot_object_detector_ros__msg__FruitClassification__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!robot_object_detector_ros__msg__FruitClassification__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
robot_object_detector_ros__msg__FruitClassification__Sequence__copy(
  const robot_object_detector_ros__msg__FruitClassification__Sequence * input,
  robot_object_detector_ros__msg__FruitClassification__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(robot_object_detector_ros__msg__FruitClassification);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    robot_object_detector_ros__msg__FruitClassification * data =
      (robot_object_detector_ros__msg__FruitClassification *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!robot_object_detector_ros__msg__FruitClassification__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          robot_object_detector_ros__msg__FruitClassification__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!robot_object_detector_ros__msg__FruitClassification__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
