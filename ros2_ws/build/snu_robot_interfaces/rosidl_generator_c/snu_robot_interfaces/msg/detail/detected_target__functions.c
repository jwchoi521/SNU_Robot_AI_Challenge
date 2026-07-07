// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from snu_robot_interfaces:msg/DetectedTarget.idl
// generated code does not contain a copyright notice
#include "snu_robot_interfaces/msg/detail/detected_target__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `object_kind`
// Member `fruit_kind`
#include "rosidl_runtime_c/string_functions.h"

bool
snu_robot_interfaces__msg__DetectedTarget__init(snu_robot_interfaces__msg__DetectedTarget * msg)
{
  if (!msg) {
    return false;
  }
  // object_kind
  if (!rosidl_runtime_c__String__init(&msg->object_kind)) {
    snu_robot_interfaces__msg__DetectedTarget__fini(msg);
    return false;
  }
  // fruit_kind
  if (!rosidl_runtime_c__String__init(&msg->fruit_kind)) {
    snu_robot_interfaces__msg__DetectedTarget__fini(msg);
    return false;
  }
  // confidence
  // bbox_x1
  // bbox_y1
  // bbox_x2
  // bbox_y2
  // bearing_deg
  // has_distance
  // distance_m
  // pick_allowed
  // target_confirmed
  return true;
}

void
snu_robot_interfaces__msg__DetectedTarget__fini(snu_robot_interfaces__msg__DetectedTarget * msg)
{
  if (!msg) {
    return;
  }
  // object_kind
  rosidl_runtime_c__String__fini(&msg->object_kind);
  // fruit_kind
  rosidl_runtime_c__String__fini(&msg->fruit_kind);
  // confidence
  // bbox_x1
  // bbox_y1
  // bbox_x2
  // bbox_y2
  // bearing_deg
  // has_distance
  // distance_m
  // pick_allowed
  // target_confirmed
}

bool
snu_robot_interfaces__msg__DetectedTarget__are_equal(const snu_robot_interfaces__msg__DetectedTarget * lhs, const snu_robot_interfaces__msg__DetectedTarget * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // object_kind
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->object_kind), &(rhs->object_kind)))
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
  // bbox_x1
  if (lhs->bbox_x1 != rhs->bbox_x1) {
    return false;
  }
  // bbox_y1
  if (lhs->bbox_y1 != rhs->bbox_y1) {
    return false;
  }
  // bbox_x2
  if (lhs->bbox_x2 != rhs->bbox_x2) {
    return false;
  }
  // bbox_y2
  if (lhs->bbox_y2 != rhs->bbox_y2) {
    return false;
  }
  // bearing_deg
  if (lhs->bearing_deg != rhs->bearing_deg) {
    return false;
  }
  // has_distance
  if (lhs->has_distance != rhs->has_distance) {
    return false;
  }
  // distance_m
  if (lhs->distance_m != rhs->distance_m) {
    return false;
  }
  // pick_allowed
  if (lhs->pick_allowed != rhs->pick_allowed) {
    return false;
  }
  // target_confirmed
  if (lhs->target_confirmed != rhs->target_confirmed) {
    return false;
  }
  return true;
}

bool
snu_robot_interfaces__msg__DetectedTarget__copy(
  const snu_robot_interfaces__msg__DetectedTarget * input,
  snu_robot_interfaces__msg__DetectedTarget * output)
{
  if (!input || !output) {
    return false;
  }
  // object_kind
  if (!rosidl_runtime_c__String__copy(
      &(input->object_kind), &(output->object_kind)))
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
  // bbox_x1
  output->bbox_x1 = input->bbox_x1;
  // bbox_y1
  output->bbox_y1 = input->bbox_y1;
  // bbox_x2
  output->bbox_x2 = input->bbox_x2;
  // bbox_y2
  output->bbox_y2 = input->bbox_y2;
  // bearing_deg
  output->bearing_deg = input->bearing_deg;
  // has_distance
  output->has_distance = input->has_distance;
  // distance_m
  output->distance_m = input->distance_m;
  // pick_allowed
  output->pick_allowed = input->pick_allowed;
  // target_confirmed
  output->target_confirmed = input->target_confirmed;
  return true;
}

snu_robot_interfaces__msg__DetectedTarget *
snu_robot_interfaces__msg__DetectedTarget__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  snu_robot_interfaces__msg__DetectedTarget * msg = (snu_robot_interfaces__msg__DetectedTarget *)allocator.allocate(sizeof(snu_robot_interfaces__msg__DetectedTarget), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(snu_robot_interfaces__msg__DetectedTarget));
  bool success = snu_robot_interfaces__msg__DetectedTarget__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
snu_robot_interfaces__msg__DetectedTarget__destroy(snu_robot_interfaces__msg__DetectedTarget * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    snu_robot_interfaces__msg__DetectedTarget__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
snu_robot_interfaces__msg__DetectedTarget__Sequence__init(snu_robot_interfaces__msg__DetectedTarget__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  snu_robot_interfaces__msg__DetectedTarget * data = NULL;

  if (size) {
    data = (snu_robot_interfaces__msg__DetectedTarget *)allocator.zero_allocate(size, sizeof(snu_robot_interfaces__msg__DetectedTarget), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = snu_robot_interfaces__msg__DetectedTarget__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        snu_robot_interfaces__msg__DetectedTarget__fini(&data[i - 1]);
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
snu_robot_interfaces__msg__DetectedTarget__Sequence__fini(snu_robot_interfaces__msg__DetectedTarget__Sequence * array)
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
      snu_robot_interfaces__msg__DetectedTarget__fini(&array->data[i]);
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

snu_robot_interfaces__msg__DetectedTarget__Sequence *
snu_robot_interfaces__msg__DetectedTarget__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  snu_robot_interfaces__msg__DetectedTarget__Sequence * array = (snu_robot_interfaces__msg__DetectedTarget__Sequence *)allocator.allocate(sizeof(snu_robot_interfaces__msg__DetectedTarget__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = snu_robot_interfaces__msg__DetectedTarget__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
snu_robot_interfaces__msg__DetectedTarget__Sequence__destroy(snu_robot_interfaces__msg__DetectedTarget__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    snu_robot_interfaces__msg__DetectedTarget__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
snu_robot_interfaces__msg__DetectedTarget__Sequence__are_equal(const snu_robot_interfaces__msg__DetectedTarget__Sequence * lhs, const snu_robot_interfaces__msg__DetectedTarget__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!snu_robot_interfaces__msg__DetectedTarget__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
snu_robot_interfaces__msg__DetectedTarget__Sequence__copy(
  const snu_robot_interfaces__msg__DetectedTarget__Sequence * input,
  snu_robot_interfaces__msg__DetectedTarget__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(snu_robot_interfaces__msg__DetectedTarget);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    snu_robot_interfaces__msg__DetectedTarget * data =
      (snu_robot_interfaces__msg__DetectedTarget *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!snu_robot_interfaces__msg__DetectedTarget__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          snu_robot_interfaces__msg__DetectedTarget__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!snu_robot_interfaces__msg__DetectedTarget__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
