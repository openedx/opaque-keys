"""
Throw-away models for testing our custom Django field classes.
"""

try:
    from django.db.models import CharField, Model
    from django.core.exceptions import ValidationError
except ImportError:  # pragma: no cover
    CharField = object
    Model = object

import six

from opaque_keys.edx.django.models import (
    BlockTypeKeyField, CourseKeyField, CreatorMixin, UsageKeyField
)


class Container(object):
    """A simple wrapper class for string-like objects."""

    def __init__(self, text):
        self.text = text

    def transform(self):
        """A toy function that does something interesting with this object's data."""
        return 'TEST_{}_TEST'.format(self.text)

    def __str__(self):
        return self.text

    def __repr__(self):
        return '<Container key={}>'.format(self.text)

    def __eq__(self, obj):
        return self.text == obj.text


#  pylint: disable=missing-docstring
class ExampleField(CreatorMixin, CharField):
    """A simple Django Field to assist in testing the CreatorMixin class."""

    def to_python(self, value):
        if isinstance(value, six.string_types):
            return Container(value)
        return value

    def get_prep_value(self, value):
        return str(value)


class ExampleModel(Model):
    """A simple Django Model to assist in testing the CreatorMixin class."""

    key = ExampleField(primary_key=True, max_length=255)


def is_edx(value):
    if value.org.lower() != 'edx':
        raise ValidationError(u'{} is not edx'.format(value))


class ComplexModel(Model):
    """A Django Model for testing Course/Usage/Location/BlockType Key fields."""

    id = CharField(primary_key=True, max_length=255)  # pylint: disable=invalid-name
    course_key = CourseKeyField(max_length=255, validators=[is_edx])
    block_type_key = BlockTypeKeyField(max_length=255, blank=True)
    usage_key = UsageKeyField(max_length=255, blank=False)
