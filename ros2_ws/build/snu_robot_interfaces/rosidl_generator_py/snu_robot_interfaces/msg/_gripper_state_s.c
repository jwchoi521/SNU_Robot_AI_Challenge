// generated from rosidl_generator_py/resource/_idl_support.c.em
// with input from snu_robot_interfaces:msg/GripperState.idl
// generated code does not contain a copyright notice
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <stdbool.h>
#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-function"
#endif
#include "numpy/ndarrayobject.h"
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif
#include "rosidl_runtime_c/visibility_control.h"
#include "snu_robot_interfaces/msg/detail/gripper_state__struct.h"
#include "snu_robot_interfaces/msg/detail/gripper_state__functions.h"

ROSIDL_GENERATOR_C_IMPORT
bool std_msgs__msg__header__convert_from_py(PyObject * _pymsg, void * _ros_message);
ROSIDL_GENERATOR_C_IMPORT
PyObject * std_msgs__msg__header__convert_to_py(void * raw_ros_message);

ROSIDL_GENERATOR_C_EXPORT
bool snu_robot_interfaces__msg__gripper_state__convert_from_py(PyObject * _pymsg, void * _ros_message)
{
  // check that the passed message is of the expected Python class
  {
    char full_classname_dest[53];
    {
      char * class_name = NULL;
      char * module_name = NULL;
      {
        PyObject * class_attr = PyObject_GetAttrString(_pymsg, "__class__");
        if (class_attr) {
          PyObject * name_attr = PyObject_GetAttrString(class_attr, "__name__");
          if (name_attr) {
            class_name = (char *)PyUnicode_1BYTE_DATA(name_attr);
            Py_DECREF(name_attr);
          }
          PyObject * module_attr = PyObject_GetAttrString(class_attr, "__module__");
          if (module_attr) {
            module_name = (char *)PyUnicode_1BYTE_DATA(module_attr);
            Py_DECREF(module_attr);
          }
          Py_DECREF(class_attr);
        }
      }
      if (!class_name || !module_name) {
        return false;
      }
      snprintf(full_classname_dest, sizeof(full_classname_dest), "%s.%s", module_name, class_name);
    }
    assert(strncmp("snu_robot_interfaces.msg._gripper_state.GripperState", full_classname_dest, 52) == 0);
  }
  snu_robot_interfaces__msg__GripperState * ros_message = _ros_message;
  {  // header
    PyObject * field = PyObject_GetAttrString(_pymsg, "header");
    if (!field) {
      return false;
    }
    if (!std_msgs__msg__header__convert_from_py(field, &ros_message->header)) {
      Py_DECREF(field);
      return false;
    }
    Py_DECREF(field);
  }
  {  // is_open
    PyObject * field = PyObject_GetAttrString(_pymsg, "is_open");
    if (!field) {
      return false;
    }
    assert(PyBool_Check(field));
    ros_message->is_open = (Py_True == field);
    Py_DECREF(field);
  }
  {  // is_closed
    PyObject * field = PyObject_GetAttrString(_pymsg, "is_closed");
    if (!field) {
      return false;
    }
    assert(PyBool_Check(field));
    ros_message->is_closed = (Py_True == field);
    Py_DECREF(field);
  }
  {  // has_object
    PyObject * field = PyObject_GetAttrString(_pymsg, "has_object");
    if (!field) {
      return false;
    }
    assert(PyBool_Check(field));
    ros_message->has_object = (Py_True == field);
    Py_DECREF(field);
  }
  {  // opening_m
    PyObject * field = PyObject_GetAttrString(_pymsg, "opening_m");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->opening_m = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // effort
    PyObject * field = PyObject_GetAttrString(_pymsg, "effort");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->effort = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }

  return true;
}

ROSIDL_GENERATOR_C_EXPORT
PyObject * snu_robot_interfaces__msg__gripper_state__convert_to_py(void * raw_ros_message)
{
  /* NOTE(esteve): Call constructor of GripperState */
  PyObject * _pymessage = NULL;
  {
    PyObject * pymessage_module = PyImport_ImportModule("snu_robot_interfaces.msg._gripper_state");
    assert(pymessage_module);
    PyObject * pymessage_class = PyObject_GetAttrString(pymessage_module, "GripperState");
    assert(pymessage_class);
    Py_DECREF(pymessage_module);
    _pymessage = PyObject_CallObject(pymessage_class, NULL);
    Py_DECREF(pymessage_class);
    if (!_pymessage) {
      return NULL;
    }
  }
  snu_robot_interfaces__msg__GripperState * ros_message = (snu_robot_interfaces__msg__GripperState *)raw_ros_message;
  {  // header
    PyObject * field = NULL;
    field = std_msgs__msg__header__convert_to_py(&ros_message->header);
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "header", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // is_open
    PyObject * field = NULL;
    field = PyBool_FromLong(ros_message->is_open ? 1 : 0);
    {
      int rc = PyObject_SetAttrString(_pymessage, "is_open", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // is_closed
    PyObject * field = NULL;
    field = PyBool_FromLong(ros_message->is_closed ? 1 : 0);
    {
      int rc = PyObject_SetAttrString(_pymessage, "is_closed", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // has_object
    PyObject * field = NULL;
    field = PyBool_FromLong(ros_message->has_object ? 1 : 0);
    {
      int rc = PyObject_SetAttrString(_pymessage, "has_object", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // opening_m
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->opening_m);
    {
      int rc = PyObject_SetAttrString(_pymessage, "opening_m", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // effort
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->effort);
    {
      int rc = PyObject_SetAttrString(_pymessage, "effort", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }

  // ownership of _pymessage is transferred to the caller
  return _pymessage;
}
