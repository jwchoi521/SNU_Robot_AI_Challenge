// generated from rosidl_generator_py/resource/_idl_support.c.em
// with input from snu_robot_interfaces:msg/DetectedTarget.idl
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
#include "snu_robot_interfaces/msg/detail/detected_target__struct.h"
#include "snu_robot_interfaces/msg/detail/detected_target__functions.h"

#include "rosidl_runtime_c/string.h"
#include "rosidl_runtime_c/string_functions.h"


ROSIDL_GENERATOR_C_EXPORT
bool snu_robot_interfaces__msg__detected_target__convert_from_py(PyObject * _pymsg, void * _ros_message)
{
  // check that the passed message is of the expected Python class
  {
    char full_classname_dest[57];
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
    assert(strncmp("snu_robot_interfaces.msg._detected_target.DetectedTarget", full_classname_dest, 56) == 0);
  }
  snu_robot_interfaces__msg__DetectedTarget * ros_message = _ros_message;
  {  // object_kind
    PyObject * field = PyObject_GetAttrString(_pymsg, "object_kind");
    if (!field) {
      return false;
    }
    assert(PyUnicode_Check(field));
    PyObject * encoded_field = PyUnicode_AsUTF8String(field);
    if (!encoded_field) {
      Py_DECREF(field);
      return false;
    }
    rosidl_runtime_c__String__assign(&ros_message->object_kind, PyBytes_AS_STRING(encoded_field));
    Py_DECREF(encoded_field);
    Py_DECREF(field);
  }
  {  // fruit_kind
    PyObject * field = PyObject_GetAttrString(_pymsg, "fruit_kind");
    if (!field) {
      return false;
    }
    assert(PyUnicode_Check(field));
    PyObject * encoded_field = PyUnicode_AsUTF8String(field);
    if (!encoded_field) {
      Py_DECREF(field);
      return false;
    }
    rosidl_runtime_c__String__assign(&ros_message->fruit_kind, PyBytes_AS_STRING(encoded_field));
    Py_DECREF(encoded_field);
    Py_DECREF(field);
  }
  {  // confidence
    PyObject * field = PyObject_GetAttrString(_pymsg, "confidence");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->confidence = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // bbox_x1
    PyObject * field = PyObject_GetAttrString(_pymsg, "bbox_x1");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->bbox_x1 = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // bbox_y1
    PyObject * field = PyObject_GetAttrString(_pymsg, "bbox_y1");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->bbox_y1 = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // bbox_x2
    PyObject * field = PyObject_GetAttrString(_pymsg, "bbox_x2");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->bbox_x2 = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // bbox_y2
    PyObject * field = PyObject_GetAttrString(_pymsg, "bbox_y2");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->bbox_y2 = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // bearing_deg
    PyObject * field = PyObject_GetAttrString(_pymsg, "bearing_deg");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->bearing_deg = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // has_distance
    PyObject * field = PyObject_GetAttrString(_pymsg, "has_distance");
    if (!field) {
      return false;
    }
    assert(PyBool_Check(field));
    ros_message->has_distance = (Py_True == field);
    Py_DECREF(field);
  }
  {  // distance_m
    PyObject * field = PyObject_GetAttrString(_pymsg, "distance_m");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->distance_m = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // pick_allowed
    PyObject * field = PyObject_GetAttrString(_pymsg, "pick_allowed");
    if (!field) {
      return false;
    }
    assert(PyBool_Check(field));
    ros_message->pick_allowed = (Py_True == field);
    Py_DECREF(field);
  }
  {  // target_confirmed
    PyObject * field = PyObject_GetAttrString(_pymsg, "target_confirmed");
    if (!field) {
      return false;
    }
    assert(PyBool_Check(field));
    ros_message->target_confirmed = (Py_True == field);
    Py_DECREF(field);
  }

  return true;
}

ROSIDL_GENERATOR_C_EXPORT
PyObject * snu_robot_interfaces__msg__detected_target__convert_to_py(void * raw_ros_message)
{
  /* NOTE(esteve): Call constructor of DetectedTarget */
  PyObject * _pymessage = NULL;
  {
    PyObject * pymessage_module = PyImport_ImportModule("snu_robot_interfaces.msg._detected_target");
    assert(pymessage_module);
    PyObject * pymessage_class = PyObject_GetAttrString(pymessage_module, "DetectedTarget");
    assert(pymessage_class);
    Py_DECREF(pymessage_module);
    _pymessage = PyObject_CallObject(pymessage_class, NULL);
    Py_DECREF(pymessage_class);
    if (!_pymessage) {
      return NULL;
    }
  }
  snu_robot_interfaces__msg__DetectedTarget * ros_message = (snu_robot_interfaces__msg__DetectedTarget *)raw_ros_message;
  {  // object_kind
    PyObject * field = NULL;
    field = PyUnicode_DecodeUTF8(
      ros_message->object_kind.data,
      strlen(ros_message->object_kind.data),
      "replace");
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "object_kind", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // fruit_kind
    PyObject * field = NULL;
    field = PyUnicode_DecodeUTF8(
      ros_message->fruit_kind.data,
      strlen(ros_message->fruit_kind.data),
      "replace");
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "fruit_kind", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // confidence
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->confidence);
    {
      int rc = PyObject_SetAttrString(_pymessage, "confidence", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // bbox_x1
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->bbox_x1);
    {
      int rc = PyObject_SetAttrString(_pymessage, "bbox_x1", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // bbox_y1
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->bbox_y1);
    {
      int rc = PyObject_SetAttrString(_pymessage, "bbox_y1", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // bbox_x2
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->bbox_x2);
    {
      int rc = PyObject_SetAttrString(_pymessage, "bbox_x2", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // bbox_y2
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->bbox_y2);
    {
      int rc = PyObject_SetAttrString(_pymessage, "bbox_y2", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // bearing_deg
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->bearing_deg);
    {
      int rc = PyObject_SetAttrString(_pymessage, "bearing_deg", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // has_distance
    PyObject * field = NULL;
    field = PyBool_FromLong(ros_message->has_distance ? 1 : 0);
    {
      int rc = PyObject_SetAttrString(_pymessage, "has_distance", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // distance_m
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->distance_m);
    {
      int rc = PyObject_SetAttrString(_pymessage, "distance_m", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // pick_allowed
    PyObject * field = NULL;
    field = PyBool_FromLong(ros_message->pick_allowed ? 1 : 0);
    {
      int rc = PyObject_SetAttrString(_pymessage, "pick_allowed", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // target_confirmed
    PyObject * field = NULL;
    field = PyBool_FromLong(ros_message->target_confirmed ? 1 : 0);
    {
      int rc = PyObject_SetAttrString(_pymessage, "target_confirmed", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }

  // ownership of _pymessage is transferred to the caller
  return _pymessage;
}
