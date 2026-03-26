"""
openedx_keys.impl.base — base classes, mixins, and re-exported exceptions.

Ported from:
  opaque_keys/__init__.py  (OpaqueKey, InvalidKeyError)
  opaque_keys/edx/keys.py  (CourseObjectMixin, i4xEncoder)
  opaque_keys/edx/locator.py  (LocalId, CheckFieldMixin)
"""
from __future__ import annotations

import json
import re
import warnings
from abc import abstractmethod
from typing import Self

from opaque_keys import InvalidKeyError, OpaqueKey  # noqa: F401 — re-exported

__all__ = [
    'OpaqueKey',
    'InvalidKeyError',
    'CourseObjectMixin',
    'i4xEncoder',
    'LocalId',
    'CheckFieldMixin',
    'BackcompatInitMixin',
]


class CourseObjectMixin:
    """
    An abstract mixin for OpaqueKey subclasses that belong to a course-like
    learning context.
    """
    __slots__ = ()

    @property
    @abstractmethod
    def course_key(self):  # pragma: no cover
        """
        Return the CourselikeKey for the course containing this object.
        """
        raise NotImplementedError()

    @abstractmethod
    def map_into_course(self, course_key) -> Self:  # pragma: no cover
        """
        Return a new key representing this object inside the given course.
        """
        raise NotImplementedError()


# Allow class name to start with a lowercase letter
class i4xEncoder(json.JSONEncoder):  # pylint: disable=invalid-name
    """
    If provided as the ``cls`` to ``json.dumps``, serializes OpaqueKey
    instances as their string representations.
    """
    def default(self, o):
        if isinstance(o, OpaqueKey):
            return str(o)
        super().default(o)
        return None


class LocalId:
    """
    Placeholder id for non-persisted XBlocks that may have hardcoded block ids.
    """
    def __init__(self, block_id=None):
        self.block_id = block_id
        super().__init__()

    def __str__(self):
        identifier = self.block_id or id(self)
        return f"localid_{identifier}"


class CheckFieldMixin:
    """
    Mixin that provides helper methods for validating key field values.
    """
    @classmethod
    def _check_key_string_field(
        cls,
        field_name,
        value,
        regexp=re.compile(r'^[a-zA-Z0-9_\-.]+$'),
    ):
        """
        Verify that a key's string field is a non-empty string matching regexp.
        """
        if not isinstance(value, str):
            raise TypeError(f"Expected a string, got {field_name}={value!r}")
        if not value or not re.match(regexp, value):
            raise ValueError(
                f"{value!r} is not a valid {cls.__name__}.{field_name} field value."
            )


class BackcompatInitMixin:
    """
    Mixin that translates deprecated constructor kwarg names to their canonical
    replacements before passing them to ``super().__init__()``.

    Subclasses declare a class-level mapping::

        RENAMED_KWARGS = {"old_name": "new_name", ...}

    The mixin emits ``DeprecationWarning`` for each old name used and raises
    ``TypeError`` if both old and new names are supplied simultaneously.
    """
    RENAMED_KWARGS: dict[str, str] = {}

    def __init__(self, **kwargs):
        for old, new in self.RENAMED_KWARGS.items():
            if old in kwargs:
                if new in kwargs:
                    raise TypeError(
                        f"Cannot supply both {old!r} (deprecated) and {new!r}"
                    )
                warnings.warn(
                    f"Keyword argument {old!r} is deprecated; use {new!r} instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                kwargs[new] = kwargs.pop(old)
        super().__init__(**kwargs)
