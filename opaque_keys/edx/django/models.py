"""
Useful django models for implementing XBlock infrastructure in django.
If Django is unavailable, none of the classes below will work as intended.
"""
import logging
import warnings

try:
    from django.core.exceptions import ValidationError
    from django.db.models import CharField
    from django.db.models.lookups import IsNull, StartsWith
except ImportError:  # pragma: no cover
    # Django is unavailable, none of the classes below will work,
    # but we don't want the class definition to fail when interpreted.
    CharField = object
    IsNull = object

import six

from opaque_keys.edx.keys import BlockTypeKey, CourseKey, UsageKey


log = logging.getLogger(__name__)


class _Creator(object):
    """
    DO NOT REUSE THIS CLASS. Provided for backwards compatibility only!

    A placeholder class that provides a way to set the attribute on the model.
    """
    def __init__(self, field):
        self.field = field

    def __get__(self, obj, type=None):  # pylint: disable=redefined-builtin
        if obj is None:
            return self  # pragma: no cover
        return obj.__dict__[self.field.name]

    def __set__(self, obj, value):
        obj.__dict__[self.field.name] = self.field.to_python(value)


# pylint: disable=missing-docstring,unused-argument
class CreatorMixin(object):
    """
    Mixin class to provide SubfieldBase functionality to django fields.
    See: https://docs.djangoproject.com/en/1.11/releases/1.8/#subfieldbase
    """
    def contribute_to_class(self, cls, name, *args, **kwargs):
        super(CreatorMixin, self).contribute_to_class(cls, name, *args, **kwargs)
        setattr(cls, name, _Creator(self))

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)


def _strip_object(key):
    """
    Strips branch and version info if the given key supports those attributes.
    """
    if hasattr(key, 'version_agnostic') and hasattr(key, 'for_branch'):
        return key.for_branch(None).version_agnostic()
    else:
        return key


def _strip_value(value, lookup='exact'):
    """
    Helper function to remove the branch and version information from the given value,
    which could be a single object or a list.
    """
    if lookup == 'in':
        stripped_value = [_strip_object(el) for el in value]
    else:
        stripped_value = _strip_object(value)
    return stripped_value


# pylint: disable=logging-format-interpolation
class OpaqueKeyField(CreatorMixin, CharField):
    """
    A django field for storing OpaqueKeys.

    The baseclass will return the value from the database as a string, rather than an instance
    of an OpaqueKey, leaving the application to determine which key subtype to parse the string
    as.

    Subclasses must specify a KEY_CLASS attribute, in which case the field will use :meth:`from_string`
    to parse the key string, and will return an instance of KEY_CLASS.
    """
    description = "An OpaqueKey object, saved to the DB in the form of a string."

    Empty = object()
    KEY_CLASS = None
    DEFAULT_MAX_LENGTH = None

    def __init__(self, *args, **kwargs):
        if self.KEY_CLASS is None:
            raise ValueError('Must specify KEY_CLASS in OpaqueKeyField subclasses')
        if self.DEFAULT_MAX_LENGTH is not None:
            kwargs.setdefault('max_length', self.DEFAULT_MAX_LENGTH)

        super(OpaqueKeyField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value is self.Empty or value is None:
            return None

        error_message = "%s is not an instance of six.string_types or %s" % (value, self.KEY_CLASS)
        assert isinstance(value, six.string_types + (self.KEY_CLASS,)), error_message
        if value == '':
            # handle empty string for models being created w/o fields populated
            return None

        if isinstance(value, six.string_types):
            if value.endswith('\n'):
                # An opaque key with a trailing newline has leaked into the DB.
                # Log and strip the value.
                log.warning(u'{}:{}:{}:to_python: Invalid key: {}. Removing trailing newline.'.format(
                    self.model._meta.db_table,  # pylint: disable=protected-access
                    self.name,
                    self.KEY_CLASS.__name__,
                    repr(value)
                ))
                value = value.rstrip()
            return self.KEY_CLASS.from_string(value)
        else:
            return value

    def get_prep_value(self, value):
        if value is self.Empty or value is None:
            return ''  # CharFields should use '' as their empty value, rather than None

        assert isinstance(value, self.KEY_CLASS), "%s is not an instance of %s" % (value, self.KEY_CLASS)
        serialized_key = six.text_type(_strip_value(value))
        if serialized_key.endswith('\n'):
            # An opaque key object serialized to a string with a trailing newline.
            # Log the value - but do not modify it.
            log.warning(u'{}:{}:{}:get_prep_value: Invalid key: {}.'.format(
                self.model._meta.db_table,  # pylint: disable=protected-access
                self.name,
                self.KEY_CLASS.__name__,
                repr(serialized_key)
            ))
        return serialized_key

    def validate(self, value, model_instance):
        """Validate Empty values, otherwise defer to the parent"""
        # raise validation error if the use of this field says it can't be blank but it is
        if not self.blank and value is self.Empty:
            raise ValidationError(self.error_messages['blank'])
        else:
            return super(OpaqueKeyField, self).validate(value, model_instance)

    def run_validators(self, value):
        """Validate Empty values, otherwise defer to the parent"""
        if value is self.Empty:
            return

        return super(OpaqueKeyField, self).run_validators(value)


class OpaqueKeyFieldEmptyLookupIsNull(IsNull):
    """
    This overrides the default __isnull model filter to help enforce the special way
    we handle null / empty values in OpaqueKeyFields.
    """
    def get_prep_lookup(self):
        raise TypeError("Use this field's .Empty member rather than None or __isnull "
                        "to query for missing objects of this type.")


try:
    #  pylint: disable=no-member
    OpaqueKeyField.register_lookup(OpaqueKeyFieldEmptyLookupIsNull)
except AttributeError:
    #  Django was not imported
    pass


class CourseKeyField(OpaqueKeyField):
    """
    A django Field that stores a CourseKey object as a string.
    """
    description = "A CourseKey object, saved to the DB in the form of a string"
    KEY_CLASS = CourseKey
    # Default to 191 characters as the maximum length of this field type,
    # because we want to support the MySQL "utf8mb4" character set (real UTF-8)
    # and the InnoDB index limit on common MySQL versions is 767 bytes
    # (191 characters * 4 bytes/character = 764 bytes)
    DEFAULT_MAX_LENGTH = 191


class UsageKeyField(OpaqueKeyField):
    """
    A django Field that stores a UsageKey object as a string.
    """
    description = "A Location object, saved to the DB in the form of a string"
    KEY_CLASS = UsageKey
    # Default to 191 characters as the maximum length of this field type,
    # because we want to support the MySQL "utf8mb4" character set (real UTF-8)
    # and the InnoDB index limit on common MySQL configurations is 767 bytes
    # (191 characters * 4 bytes/character = 764 bytes)
    DEFAULT_MAX_LENGTH = 191


class UsageKeyCourseLookup(StartsWith):
    """
    Allows efficiently querying the course that a UsageKey belongs to,
    without requiring that the CourseKey is stored in a separate column.

    This only works with UsageKeys that contain the full CourseKey in
    their serialized form, preceding any usage-specific identifiers.

    Usage: my_model.objects.filter(usage_key__course=course_key)
    """
    lookup_name = 'course'

    def get_prep_lookup(self):
        """
        Prepare the right-hand-side value of the 'field__course = RHS' expression

        Convert from a CourseKey objects to a string like
        'block-v1:the+course_here+type@' which will be converted to SQL like:
            WHERE usage_id LIKE 'block-v1:the+course_here+type@%'
        """
        course_key = self.rhs
        if not isinstance(course_key, CourseKey):
            raise TypeError("The __course lookup requires a CourseKey value.")
        marker_str = 'MaRkErZZZ'  # a short sequence that is allowed in a key but unlikely to occur in the course ID
        example_usage_key = course_key.make_usage_key(marker_str, marker_str)
        usage_key_prefix = six.text_type(example_usage_key).partition(marker_str)[0]
        if course_key._to_string() not in usage_key_prefix:  # pylint: disable=protected-access
            raise TypeError("The CourseKey provided does not support __course lookups.")
        return usage_key_prefix

    def get_rhs_op(self, connection, rhs):
        return connection.operators['startswith'] % rhs


try:
    #  pylint: disable=no-member
    UsageKeyField.register_lookup(UsageKeyCourseLookup)
except AttributeError:
    #  Django was not imported
    pass


class LocationKeyField(UsageKeyField):
    """
    A django Field that stores a UsageKey object as a string.
    """
    def __init__(self, *args, **kwargs):
        warnings.warn("LocationKeyField is deprecated. Please use UsageKeyField instead.", stacklevel=2)
        super(LocationKeyField, self).__init__(*args, **kwargs)


class BlockTypeKeyField(OpaqueKeyField):
    """
    A django Field that stores a BlockTypeKey object as a string.
    """
    description = "A BlockTypeKey object, saved to the DB in the form of a string."
    KEY_CLASS = BlockTypeKey
    DEFAULT_MAX_LENGTH = 128
