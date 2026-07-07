# generated from rosidl_generator_py/resource/_idl.py.em
# with input from snu_robot_interfaces:msg/PerceivedObject.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_PerceivedObject(type):
    """Metaclass of message 'PerceivedObject'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
        'ROLE_UNKNOWN': 0,
        'ROLE_TARGET': 1,
        'ROLE_OBSTACLE': 2,
        'ROLE_IGNORE': 3,
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
                'snu_robot_interfaces.msg.PerceivedObject')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__perceived_object
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__perceived_object
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__perceived_object
            cls._TYPE_SUPPORT = module.type_support_msg__msg__perceived_object
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__perceived_object

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
            'ROLE_UNKNOWN': cls.__constants['ROLE_UNKNOWN'],
            'ROLE_TARGET': cls.__constants['ROLE_TARGET'],
            'ROLE_OBSTACLE': cls.__constants['ROLE_OBSTACLE'],
            'ROLE_IGNORE': cls.__constants['ROLE_IGNORE'],
        }

    @property
    def ROLE_UNKNOWN(self):
        """Message constant 'ROLE_UNKNOWN'."""
        return Metaclass_PerceivedObject.__constants['ROLE_UNKNOWN']

    @property
    def ROLE_TARGET(self):
        """Message constant 'ROLE_TARGET'."""
        return Metaclass_PerceivedObject.__constants['ROLE_TARGET']

    @property
    def ROLE_OBSTACLE(self):
        """Message constant 'ROLE_OBSTACLE'."""
        return Metaclass_PerceivedObject.__constants['ROLE_OBSTACLE']

    @property
    def ROLE_IGNORE(self):
        """Message constant 'ROLE_IGNORE'."""
        return Metaclass_PerceivedObject.__constants['ROLE_IGNORE']


class PerceivedObject(metaclass=Metaclass_PerceivedObject):
    """
    Message class 'PerceivedObject'.

    Constants:
      ROLE_UNKNOWN
      ROLE_TARGET
      ROLE_OBSTACLE
      ROLE_IGNORE
    """

    __slots__ = [
        '_object_kind',
        '_fruit_kind',
        '_navigation_role',
        '_confidence',
        '_bbox_x1',
        '_bbox_y1',
        '_bbox_x2',
        '_bbox_y2',
        '_bearing_deg',
        '_has_distance',
        '_distance_m',
        '_obstacle_radius_m',
        '_pick_allowed',
        '_target_confirmed',
    ]

    _fields_and_field_types = {
        'object_kind': 'string',
        'fruit_kind': 'string',
        'navigation_role': 'uint8',
        'confidence': 'float',
        'bbox_x1': 'float',
        'bbox_y1': 'float',
        'bbox_x2': 'float',
        'bbox_y2': 'float',
        'bearing_deg': 'float',
        'has_distance': 'boolean',
        'distance_m': 'float',
        'obstacle_radius_m': 'float',
        'pick_allowed': 'boolean',
        'target_confirmed': 'boolean',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.object_kind = kwargs.get('object_kind', str())
        self.fruit_kind = kwargs.get('fruit_kind', str())
        self.navigation_role = kwargs.get('navigation_role', int())
        self.confidence = kwargs.get('confidence', float())
        self.bbox_x1 = kwargs.get('bbox_x1', float())
        self.bbox_y1 = kwargs.get('bbox_y1', float())
        self.bbox_x2 = kwargs.get('bbox_x2', float())
        self.bbox_y2 = kwargs.get('bbox_y2', float())
        self.bearing_deg = kwargs.get('bearing_deg', float())
        self.has_distance = kwargs.get('has_distance', bool())
        self.distance_m = kwargs.get('distance_m', float())
        self.obstacle_radius_m = kwargs.get('obstacle_radius_m', float())
        self.pick_allowed = kwargs.get('pick_allowed', bool())
        self.target_confirmed = kwargs.get('target_confirmed', bool())

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
        if self.object_kind != other.object_kind:
            return False
        if self.fruit_kind != other.fruit_kind:
            return False
        if self.navigation_role != other.navigation_role:
            return False
        if self.confidence != other.confidence:
            return False
        if self.bbox_x1 != other.bbox_x1:
            return False
        if self.bbox_y1 != other.bbox_y1:
            return False
        if self.bbox_x2 != other.bbox_x2:
            return False
        if self.bbox_y2 != other.bbox_y2:
            return False
        if self.bearing_deg != other.bearing_deg:
            return False
        if self.has_distance != other.has_distance:
            return False
        if self.distance_m != other.distance_m:
            return False
        if self.obstacle_radius_m != other.obstacle_radius_m:
            return False
        if self.pick_allowed != other.pick_allowed:
            return False
        if self.target_confirmed != other.target_confirmed:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def object_kind(self):
        """Message field 'object_kind'."""
        return self._object_kind

    @object_kind.setter
    def object_kind(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'object_kind' field must be of type 'str'"
        self._object_kind = value

    @builtins.property
    def fruit_kind(self):
        """Message field 'fruit_kind'."""
        return self._fruit_kind

    @fruit_kind.setter
    def fruit_kind(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'fruit_kind' field must be of type 'str'"
        self._fruit_kind = value

    @builtins.property
    def navigation_role(self):
        """Message field 'navigation_role'."""
        return self._navigation_role

    @navigation_role.setter
    def navigation_role(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'navigation_role' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'navigation_role' field must be an unsigned integer in [0, 255]"
        self._navigation_role = value

    @builtins.property
    def confidence(self):
        """Message field 'confidence'."""
        return self._confidence

    @confidence.setter
    def confidence(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'confidence' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'confidence' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._confidence = value

    @builtins.property
    def bbox_x1(self):
        """Message field 'bbox_x1'."""
        return self._bbox_x1

    @bbox_x1.setter
    def bbox_x1(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'bbox_x1' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'bbox_x1' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._bbox_x1 = value

    @builtins.property
    def bbox_y1(self):
        """Message field 'bbox_y1'."""
        return self._bbox_y1

    @bbox_y1.setter
    def bbox_y1(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'bbox_y1' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'bbox_y1' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._bbox_y1 = value

    @builtins.property
    def bbox_x2(self):
        """Message field 'bbox_x2'."""
        return self._bbox_x2

    @bbox_x2.setter
    def bbox_x2(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'bbox_x2' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'bbox_x2' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._bbox_x2 = value

    @builtins.property
    def bbox_y2(self):
        """Message field 'bbox_y2'."""
        return self._bbox_y2

    @bbox_y2.setter
    def bbox_y2(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'bbox_y2' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'bbox_y2' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._bbox_y2 = value

    @builtins.property
    def bearing_deg(self):
        """Message field 'bearing_deg'."""
        return self._bearing_deg

    @bearing_deg.setter
    def bearing_deg(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'bearing_deg' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'bearing_deg' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._bearing_deg = value

    @builtins.property
    def has_distance(self):
        """Message field 'has_distance'."""
        return self._has_distance

    @has_distance.setter
    def has_distance(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'has_distance' field must be of type 'bool'"
        self._has_distance = value

    @builtins.property
    def distance_m(self):
        """Message field 'distance_m'."""
        return self._distance_m

    @distance_m.setter
    def distance_m(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'distance_m' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'distance_m' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._distance_m = value

    @builtins.property
    def obstacle_radius_m(self):
        """Message field 'obstacle_radius_m'."""
        return self._obstacle_radius_m

    @obstacle_radius_m.setter
    def obstacle_radius_m(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'obstacle_radius_m' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'obstacle_radius_m' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._obstacle_radius_m = value

    @builtins.property
    def pick_allowed(self):
        """Message field 'pick_allowed'."""
        return self._pick_allowed

    @pick_allowed.setter
    def pick_allowed(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'pick_allowed' field must be of type 'bool'"
        self._pick_allowed = value

    @builtins.property
    def target_confirmed(self):
        """Message field 'target_confirmed'."""
        return self._target_confirmed

    @target_confirmed.setter
    def target_confirmed(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'target_confirmed' field must be of type 'bool'"
        self._target_confirmed = value
