# generated from rosidl_generator_py/resource/_idl.py.em
# with input from gesture_management:srv/PlayRecording.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_PlayRecording_Request(type):
    """Metaclass of message 'PlayRecording_Request'."""

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
            module = import_type_support('gesture_management')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'gesture_management.srv.PlayRecording_Request')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__srv__play_recording__request
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__srv__play_recording__request
            cls._CONVERT_TO_PY = module.convert_to_py_msg__srv__play_recording__request
            cls._TYPE_SUPPORT = module.type_support_msg__srv__play_recording__request
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__srv__play_recording__request

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class PlayRecording_Request(metaclass=Metaclass_PlayRecording_Request):
    """Message class 'PlayRecording_Request'."""

    __slots__ = [
        '_recording_name',
        '_output_topic',
        '_replay_speed',
        '_repeat_mode',
        '_repeat_count',
        '_interval_s',
    ]

    _fields_and_field_types = {
        'recording_name': 'string',
        'output_topic': 'string',
        'replay_speed': 'float',
        'repeat_mode': 'string',
        'repeat_count': 'int32',
        'interval_s': 'float',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.recording_name = kwargs.get('recording_name', str())
        self.output_topic = kwargs.get('output_topic', str())
        self.replay_speed = kwargs.get('replay_speed', float())
        self.repeat_mode = kwargs.get('repeat_mode', str())
        self.repeat_count = kwargs.get('repeat_count', int())
        self.interval_s = kwargs.get('interval_s', float())

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
        if self.recording_name != other.recording_name:
            return False
        if self.output_topic != other.output_topic:
            return False
        if self.replay_speed != other.replay_speed:
            return False
        if self.repeat_mode != other.repeat_mode:
            return False
        if self.repeat_count != other.repeat_count:
            return False
        if self.interval_s != other.interval_s:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def recording_name(self):
        """Message field 'recording_name'."""
        return self._recording_name

    @recording_name.setter
    def recording_name(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'recording_name' field must be of type 'str'"
        self._recording_name = value

    @builtins.property
    def output_topic(self):
        """Message field 'output_topic'."""
        return self._output_topic

    @output_topic.setter
    def output_topic(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'output_topic' field must be of type 'str'"
        self._output_topic = value

    @builtins.property
    def replay_speed(self):
        """Message field 'replay_speed'."""
        return self._replay_speed

    @replay_speed.setter
    def replay_speed(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'replay_speed' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'replay_speed' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._replay_speed = value

    @builtins.property
    def repeat_mode(self):
        """Message field 'repeat_mode'."""
        return self._repeat_mode

    @repeat_mode.setter
    def repeat_mode(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'repeat_mode' field must be of type 'str'"
        self._repeat_mode = value

    @builtins.property
    def repeat_count(self):
        """Message field 'repeat_count'."""
        return self._repeat_count

    @repeat_count.setter
    def repeat_count(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'repeat_count' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'repeat_count' field must be an integer in [-2147483648, 2147483647]"
        self._repeat_count = value

    @builtins.property
    def interval_s(self):
        """Message field 'interval_s'."""
        return self._interval_s

    @interval_s.setter
    def interval_s(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'interval_s' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'interval_s' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._interval_s = value


# Import statements for member types

# already imported above
# import builtins

# already imported above
# import rosidl_parser.definition


class Metaclass_PlayRecording_Response(type):
    """Metaclass of message 'PlayRecording_Response'."""

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
            module = import_type_support('gesture_management')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'gesture_management.srv.PlayRecording_Response')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__srv__play_recording__response
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__srv__play_recording__response
            cls._CONVERT_TO_PY = module.convert_to_py_msg__srv__play_recording__response
            cls._TYPE_SUPPORT = module.type_support_msg__srv__play_recording__response
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__srv__play_recording__response

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class PlayRecording_Response(metaclass=Metaclass_PlayRecording_Response):
    """Message class 'PlayRecording_Response'."""

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


class Metaclass_PlayRecording(type):
    """Metaclass of service 'PlayRecording'."""

    _TYPE_SUPPORT = None

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('gesture_management')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'gesture_management.srv.PlayRecording')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._TYPE_SUPPORT = module.type_support_srv__srv__play_recording

            from gesture_management.srv import _play_recording
            if _play_recording.Metaclass_PlayRecording_Request._TYPE_SUPPORT is None:
                _play_recording.Metaclass_PlayRecording_Request.__import_type_support__()
            if _play_recording.Metaclass_PlayRecording_Response._TYPE_SUPPORT is None:
                _play_recording.Metaclass_PlayRecording_Response.__import_type_support__()


class PlayRecording(metaclass=Metaclass_PlayRecording):
    from gesture_management.srv._play_recording import PlayRecording_Request as Request
    from gesture_management.srv._play_recording import PlayRecording_Response as Response

    def __init__(self):
        raise NotImplementedError('Service classes can not be instantiated')
