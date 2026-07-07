# generated from rosidl_generator_py/resource/_idl.py.em
# with input from snu_robot_interfaces:msg/GripperState.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_GripperState(type):
    """Metaclass of message 'GripperState'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('snu_robot_interfaces')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'snu_robot_interfaces.msg.GripperState')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__gripper_state
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__gripper_state
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__gripper_state
            cls._TYPE_SUPPORT = module.type_support_msg__msg__gripper_state
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__gripper_state

            from std_msgs.msg import Header
            if Header.__class__._TYPE_SUPPORT is None:
                Header.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class GripperState(metaclass=Metaclass_GripperState):
    """Message class 'GripperState'."""

    __slots__ = [
        '_header',
        '_is_open',
        '_is_closed',
        '_has_object',
        '_opening_m',
        '_effort',
    ]

    _fields_and_field_types = {
        'header': 'std_msgs/Header',
        'is_open': 'boolean',
        'is_closed': 'boolean',
        'has_object': 'boolean',
        'opening_m': 'float',
        'effort': 'float',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.NamespacedType(['std_msgs', 'msg'], 'Header'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        from std_msgs.msg import Header
        self.header = kwargs.get('header', Header())
        self.is_open = kwargs.get('is_open', bool())
        self.is_closed = kwargs.get('is_closed', bool())
        self.has_object = kwargs.get('has_object', bool())
        self.opening_m = kwargs.get('opening_m', float())
        self.effort = kwargs.get('effort', float())

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.__slots__, self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s[1:] + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.header != other.header:
            return False
        if self.is_open != other.is_open:
            return False
        if self.is_closed != other.is_closed:
            return False
        if self.has_object != other.has_object:
            return False
        if self.opening_m != other.opening_m:
            return False
        if self.effort != other.effort:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def header(self):
        """Message field 'header'."""
        return self._header

    @header.setter
    def header(self, value):
        if __debug__:
            from std_msgs.msg import Header
            assert \
                isinstance(value, Header), \
                "The 'header' field must be a sub message of type 'Header'"
        self._header = value

    @builtins.property
    def is_open(self):
        """Message field 'is_open'."""
        return self._is_open

    @is_open.setter
    def is_open(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'is_open' field must be of type 'bool'"
        self._is_open = value

    @builtins.property
    def is_closed(self):
        """Message field 'is_closed'."""
        return self._is_closed

    @is_closed.setter
    def is_closed(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'is_closed' field must be of type 'bool'"
        self._is_closed = value

    @builtins.property
    def has_object(self):
        """Message field 'has_object'."""
        return self._has_object

    @has_object.setter
    def has_object(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'has_object' field must be of type 'bool'"
        self._has_object = value

    @builtins.property
    def opening_m(self):
        """Message field 'opening_m'."""
        return self._opening_m

    @opening_m.setter
    def opening_m(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'opening_m' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'opening_m' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._opening_m = value

    @builtins.property
    def effort(self):
        """Message field 'effort'."""
        return self._effort

    @effort.setter
    def effort(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'effort' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'effort' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._effort = value
