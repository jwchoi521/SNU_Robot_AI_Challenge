// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from snu_robot_interfaces:msg/FourWheelCommand.idl
// generated code does not contain a copyright notice

#ifndef SNU_ROBOT_INTERFACES__MSG__DETAIL__FOUR_WHEEL_COMMAND__FUNCTIONS_H_
#define SNU_ROBOT_INTERFACES__MSG__DETAIL__FOUR_WHEEL_COMMAND__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "snu_robot_interfaces/msg/rosidl_generator_c__visibility_control.h"

#include "snu_robot_interfaces/msg/detail/four_wheel_command__struct.h"

/// Initialize msg/FourWheelCommand message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * snu_robot_interfaces__msg__FourWheelCommand
 * )) before or use
 * snu_robot_interfaces__msg__FourWheelCommand__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_snu_robot_interfaces
bool
snu_robot_interfaces__msg__FourWheelCommand__init(snu_robot_interfaces__msg__FourWheelCommand * msg);

/// Finalize msg/FourWheelCommand message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_snu_robot_interfaces
void
snu_robot_interfaces__msg__FourWheelCommand__fini(snu_robot_interfaces__msg__FourWheelCommand * msg);

/// Create msg/FourWheelCommand message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * snu_robot_interfaces__msg__FourWheelCommand__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_snu_robot_interfaces
snu_robot_interfaces__msg__FourWheelCommand *
snu_robot_interfaces__msg__FourWheelCommand__create();

/// Destroy msg/FourWheelCommand message.
/**
 * It calls
 * snu_robot_interfaces__msg__FourWheelCommand__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_snu_robot_interfaces
void
snu_robot_interfaces__msg__FourWheelCommand__destroy(snu_robot_interfaces__msg__FourWheelCommand * msg);

/// Check for msg/FourWheelCommand message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_snu_robot_interfaces
bool
snu_robot_interfaces__msg__FourWheelCommand__are_equal(const snu_robot_interfaces__msg__FourWheelCommand * lhs, const snu_robot_interfaces__msg__FourWheelCommand * rhs);

/// Copy a msg/FourWheelCommand message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_snu_robot_interfaces
bool
snu_robot_interfaces__msg__FourWheelCommand__copy(
  const snu_robot_interfaces__msg__FourWheelCommand * input,
  snu_robot_interfaces__msg__FourWheelCommand * output);

/// Initialize array of msg/FourWheelCommand messages.
/**
 * It allocates the memory for the number of elements and calls
 * snu_robot_interfaces__msg__FourWheelCommand__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_snu_robot_interfaces
bool
snu_robot_interfaces__msg__FourWheelCommand__Sequence__init(snu_robot_interfaces__msg__FourWheelCommand__Sequence * array, size_t size);

/// Finalize array of msg/FourWheelCommand messages.
/**
 * It calls
 * snu_robot_interfaces__msg__FourWheelCommand__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_snu_robot_interfaces
void
snu_robot_interfaces__msg__FourWheelCommand__Sequence__fini(snu_robot_interfaces__msg__FourWheelCommand__Sequence * array);

/// Create array of msg/FourWheelCommand messages.
/**
 * It allocates the memory for the array and calls
 * snu_robot_interfaces__msg__FourWheelCommand__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_snu_robot_interfaces
snu_robot_interfaces__msg__FourWheelCommand__Sequence *
snu_robot_interfaces__msg__FourWheelCommand__Sequence__create(size_t size);

/// Destroy array of msg/FourWheelCommand messages.
/**
 * It calls
 * snu_robot_interfaces__msg__FourWheelCommand__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_snu_robot_interfaces
void
snu_robot_interfaces__msg__FourWheelCommand__Sequence__destroy(snu_robot_interfaces__msg__FourWheelCommand__Sequence * array);

/// Check for msg/FourWheelCommand message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_snu_robot_interfaces
bool
snu_robot_interfaces__msg__FourWheelCommand__Sequence__are_equal(const snu_robot_interfaces__msg__FourWheelCommand__Sequence * lhs, const snu_robot_interfaces__msg__FourWheelCommand__Sequence * rhs);

/// Copy an array of msg/FourWheelCommand messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_snu_robot_interfaces
bool
snu_robot_interfaces__msg__FourWheelCommand__Sequence__copy(
  const snu_robot_interfaces__msg__FourWheelCommand__Sequence * input,
  snu_robot_interfaces__msg__FourWheelCommand__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // SNU_ROBOT_INTERFACES__MSG__DETAIL__FOUR_WHEEL_COMMAND__FUNCTIONS_H_
