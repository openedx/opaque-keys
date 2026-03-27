"""
openedx_keys.impl.fields — Django model field classes.

Renames from opaque_keys.edx.django.models:
  _Creator                     -> _Creator                     (unchanged)
  CreatorMixin                 -> CreatorMixin                  (unchanged)
  OpaqueKeyField               -> OpaqueKeyField               (unchanged)
  OpaqueKeyFieldEmptyLookupIsNull -> OpaqueKeyFieldEmptyLookupIsNull (unchanged)
  LearningContextKeyField      -> ContextKeyField
  CourseKeyField               -> CourseKeyField               (unchanged name, KEY_CLASS updated)
  UsageKeyField                -> UsageKeyField                (unchanged)
  ContainerKeyField            -> ContainerKeyField            (unchanged)
  CollectionKeyField           -> CollectionKeyField           (unchanged name, KEY_CLASS updated)
"""
from __future__ import annotations

import logging

try:
    from django.core.exceptions import ValidationError
    from django.db.models import CharField, Field
    from django.db.models.lookups import IsNull
except ImportError:  # pragma: no cover
    CharField = object  # type: ignore[assignment, misc]
    IsNull = object  # type: ignore[assignment]

from opaque_keys import OpaqueKey
from openedx_keys.impl.collections import CollectionKey
from openedx_keys.impl.containers import ContainerKey
from openedx_keys.impl.contexts import ContextKey, CourselikeKey
from openedx_keys.impl.usages import UsageKey

log = logging.getLogger(__name__)

__all__ = [
    '_Creator',
    'CreatorMixin',
    'OpaqueKeyField',
    'OpaqueKeyFieldEmptyLookupIsNull',
    'ContextKeyField',
    'CourseKeyField',
    'UsageKeyField',
    'ContainerKeyField',
    'CollectionKeyField',
]


class _Creator:
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


# pylint: disable=unused-argument
class CreatorMixin:
    """
    Mixin class to provide SubfieldBase functionality to django fields.
    See: https://docs.djangoproject.com/en/1.11/releases/1.8/#subfieldbase
    """

    def contribute_to_class(self, cls, name, *args, **kwargs):
        super().contribute_to_class(cls, name, *args, **kwargs)
        setattr(cls, name, _Creator(self))

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)


def _strip_object(key):
    """Strip branch and version info if the given key supports those attributes."""
    if hasattr(key, 'version_agnostic') and hasattr(key, 'for_branch'):
        return key.for_branch(None).version_agnostic()
    return key


def _strip_value(value, lookup='exact'):
    """Remove branch and version information from the given value."""
    if lookup == 'in':
        stripped_value = [_strip_object(el) for el in value]
    else:
        stripped_value = _strip_object(value)
    return stripped_value


class OpaqueKeyField(CreatorMixin, CharField):
    """
    A django field for storing OpaqueKeys.

    Subclasses must specify a KEY_CLASS attribute; the field will use
    :meth:`from_string` to parse the key string and return an instance
    of KEY_CLASS.
    """
    description = "An OpaqueKey object, saved to the DB in the form of a string."

    Empty = object()
    KEY_CLASS: type[OpaqueKey]

    def __init__(self, *args, **kwargs):
        if self.KEY_CLASS is None:
            raise ValueError(  # pragma: no cover
                'Must specify KEY_CLASS in OpaqueKeyField subclasses'
            )
        kwargs.setdefault("max_length", 255)
        self.case_sensitive = kwargs.pop("case_sensitive", False)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value is self.Empty or value is None:
            return None

        error_message = f"{value} is not an instance of str or {self.KEY_CLASS}"
        assert isinstance(
            value,
            (str,) if self.KEY_CLASS is None else (str, self.KEY_CLASS),
        ), error_message
        if value == '':
            return None

        if isinstance(value, str):
            if value.endswith('\n'):
                log.warning(
                    '%(db_table)s:%(name)s:%(key_class_name)s:to_python: '
                    'Invalid key: %(value)s. Removing trailing newline.',
                    {
                        'db_table': self.model._meta.db_table,  # pylint: disable=protected-access
                        'name': self.name,
                        'key_class_name': self.KEY_CLASS.__name__,
                        'value': repr(value),
                    }
                )
                value = value.rstrip()
            return self.KEY_CLASS.from_string(value)
        return value

    def get_prep_value(self, value):
        if value is self.Empty or value is None:
            return ''

        if isinstance(value, str):
            value = self.KEY_CLASS.from_string(value)
        assert isinstance(value, self.KEY_CLASS), (
            f"{value} is not an instance of {self.KEY_CLASS}"
        )
        serialized_key = str(_strip_value(value))
        if serialized_key.endswith('\n'):
            log.warning(
                '%(db_table)s:%(name)s:%(key_class_name)s:get_prep_value: '
                'Invalid key: %(serialized_key)s.',
                {
                    'db_table': self.model._meta.db_table,  # pylint: disable=protected-access
                    'name': self.name,
                    'key_class_name': self.KEY_CLASS.__name__,
                    'serialized_key': repr(serialized_key),
                }
            )
        return serialized_key

    def validate(self, value, model_instance):
        """Validate Empty values, otherwise defer to the parent."""
        if self.blank or value is not self.Empty:
            return super().validate(value, model_instance)  # pylint: disable=no-member
        raise ValidationError(self.error_messages['blank'])

    def run_validators(self, value):
        """Validate Empty values, otherwise defer to the parent."""
        if value is self.Empty:
            return None
        return super().run_validators(value)  # pylint: disable=no-member

    def db_parameters(self, connection):
        """
        Return database parameters for this field including collation info.
        """
        db_params = Field.db_parameters(self, connection)

        if connection.vendor == "sqlite":
            db_params["collation"] = "BINARY" if self.case_sensitive else "NOCASE"
        elif connection.vendor == "mysql":  # pragma: no cover
            db_params["collation"] = (
                "utf8mb4_bin" if self.case_sensitive else "utf8mb4_unicode_ci"
            )
        elif connection.vendor == "postgresql":  # pragma: no cover
            pass

        return db_params

    def deconstruct(self):
        """Serialize this field for migrations."""
        name, path, args, kwargs = super().deconstruct()  # pylint: disable=no-member
        if self.case_sensitive:
            kwargs["case_sensitive"] = True
        return name, path, args, kwargs


class OpaqueKeyFieldEmptyLookupIsNull(IsNull):
    """
    Overrides the default __isnull model filter for OpaqueKeyFields.
    """

    def get_prep_lookup(self):
        raise TypeError(
            "Use this field's .Empty member rather than None or __isnull "
            "to query for missing objects of this type."
        )


try:
    OpaqueKeyField.register_lookup(OpaqueKeyFieldEmptyLookupIsNull)
except AttributeError:
    #  Django was not imported
    pass


class ContextKeyField(OpaqueKeyField):
    """
    A django Field that stores a ContextKey object as a string.
    Renamed from LearningContextKeyField.

    Use this for code that may deal with any learning context (courses,
    libraries, etc.). For course-only code, use CourseKeyField instead.
    """
    description = "A ContextKey object, saved to the DB in the form of a string"
    KEY_CLASS = ContextKey
    _pyi_private_set_type: ContextKey | str | None
    _pyi_private_get_type: ContextKey | None


class CourseKeyField(OpaqueKeyField):
    """
    A django Field that stores a CourselikeKey object as a string.
    Unchanged name; KEY_CLASS updated to CourselikeKey.
    """
    description = "A CourselikeKey object, saved to the DB in the form of a string"
    KEY_CLASS = CourselikeKey
    _pyi_private_set_type: CourselikeKey | str | None
    _pyi_private_get_type: CourselikeKey | None


class UsageKeyField(OpaqueKeyField):
    """
    A django Field that stores a UsageKey object as a string. Unchanged name.
    """
    description = "A UsageKey object, saved to the DB in the form of a string"
    KEY_CLASS = UsageKey
    _pyi_private_set_type: UsageKey | str | None
    _pyi_private_get_type: UsageKey | None


class ContainerKeyField(OpaqueKeyField):
    """
    A django Field that stores a ContainerKey object as a string. Unchanged name.
    """
    description = "A ContainerKey object, saved to the DB in the form of a string"
    KEY_CLASS = ContainerKey
    _pyi_private_set_type: ContainerKey | str | None
    _pyi_private_get_type: ContainerKey | None


class CollectionKeyField(OpaqueKeyField):
    """
    A django Field that stores a CollectionKey object as a string.
    Unchanged name; KEY_CLASS updated to new CollectionKey.
    """
    description = "A CollectionKey object, saved to the DB in the form of a string"
    KEY_CLASS = CollectionKey
    _pyi_private_set_type: CollectionKey | str | None
    _pyi_private_get_type: CollectionKey | None
