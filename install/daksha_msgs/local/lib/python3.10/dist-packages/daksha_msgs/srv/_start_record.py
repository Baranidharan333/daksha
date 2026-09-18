# generated from rosidl_generator_py/resource/_idl.py.em
# with input from daksha_msgs:srv/StartRecord.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_StartRecord_Request(type):
    """Metaclass of message 'StartRecord_Request'."""

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
            module = import_type_support('daksha_msgs')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'daksha_msgs.srv.StartRecord_Request')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__srv__start_record__request
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__srv__start_record__request
            cls._CONVERT_TO_PY = module.convert_to_py_msg__srv__start_record__request
            cls._TYPE_SUPPORT = module.type_support_msg__srv__start_record__request
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__srv__start_record__request

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class StartRecord_Request(metaclass=Metaclass_StartRecord_Request):
    """Message class 'StartRecord_Request'."""

    __slots__ = [
        '_dataset_name',
        '_episode_length',
        '_record_hz',
        '_max_episodes',
    ]

    _fields_and_field_types = {
        'dataset_name': 'string',
        'episode_length': 'int32',
        'record_hz': 'float',
        'max_episodes': 'int32',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.dataset_name = kwargs.get('dataset_name', str())
        self.episode_length = kwargs.get('episode_length', int())
        self.record_hz = kwargs.get('record_hz', float())
        self.max_episodes = kwargs.get('max_episodes', int())

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
        if self.dataset_name != other.dataset_name:
            return False
        if self.episode_length != other.episode_length:
            return False
        if self.record_hz != other.record_hz:
            return False
        if self.max_episodes != other.max_episodes:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def dataset_name(self):
        """Message field 'dataset_name'."""
        return self._dataset_name

    @dataset_name.setter
    def dataset_name(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'dataset_name' field must be of type 'str'"
        self._dataset_name = value

    @builtins.property
    def episode_length(self):
        """Message field 'episode_length'."""
        return self._episode_length

    @episode_length.setter
    def episode_length(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'episode_length' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'episode_length' field must be an integer in [-2147483648, 2147483647]"
        self._episode_length = value

    @builtins.property
    def record_hz(self):
        """Message field 'record_hz'."""
        return self._record_hz

    @record_hz.setter
    def record_hz(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'record_hz' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'record_hz' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._record_hz = value

    @builtins.property
    def max_episodes(self):
        """Message field 'max_episodes'."""
        return self._max_episodes

    @max_episodes.setter
    def max_episodes(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'max_episodes' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'max_episodes' field must be an integer in [-2147483648, 2147483647]"
        self._max_episodes = value


# Import statements for member types

# already imported above
# import builtins

# already imported above
# import rosidl_parser.definition


class Metaclass_StartRecord_Response(type):
    """Metaclass of message 'StartRecord_Response'."""

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
            module = import_type_support('daksha_msgs')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'daksha_msgs.srv.StartRecord_Response')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__srv__start_record__response
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__srv__start_record__response
            cls._CONVERT_TO_PY = module.convert_to_py_msg__srv__start_record__response
            cls._TYPE_SUPPORT = module.type_support_msg__srv__start_record__response
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__srv__start_record__response

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class StartRecord_Response(metaclass=Metaclass_StartRecord_Response):
    """Message class 'StartRecord_Response'."""

    __slots__ = [
        '_success',
        '_message',
    ]

    _fields_and_field_types = {
        'success': 'boolean',
        'message': 'string',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.success = kwargs.get('success', bool())
        self.message = kwargs.get('message', str())

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
        if self.success != other.success:
            return False
        if self.message != other.message:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def success(self):
        """Message field 'success'."""
        return self._success

    @success.setter
    def success(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'success' field must be of type 'bool'"
        self._success = value

    @builtins.property
    def message(self):
        """Message field 'message'."""
        return self._message

    @message.setter
    def message(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'message' field must be of type 'str'"
        self._message = value


class Metaclass_StartRecord(type):
    """Metaclass of service 'StartRecord'."""

    _TYPE_SUPPORT = None

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('daksha_msgs')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'daksha_msgs.srv.StartRecord')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._TYPE_SUPPORT = module.type_support_srv__srv__start_record

            from daksha_msgs.srv import _start_record
            if _start_record.Metaclass_StartRecord_Request._TYPE_SUPPORT is None:
                _start_record.Metaclass_StartRecord_Request.__import_type_support__()
            if _start_record.Metaclass_StartRecord_Response._TYPE_SUPPORT is None:
                _start_record.Metaclass_StartRecord_Response.__import_type_support__()


class StartRecord(metaclass=Metaclass_StartRecord):
    from daksha_msgs.srv._start_record import StartRecord_Request as Request
    from daksha_msgs.srv._start_record import StartRecord_Response as Response

    def __init__(self):
        raise NotImplementedError('Service classes can not be instantiated')
