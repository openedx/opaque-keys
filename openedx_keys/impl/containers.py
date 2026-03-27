"""
openedx_keys.impl.containers — container key hierarchy.

Renames from opaque_keys.edx:
  ContainerKey            -> ContainerKey (unchanged name, was abstract in keys.py)
  LibraryContainerLocator -> LibraryContainerKey
"""
from __future__ import annotations

import re
import warnings
from abc import abstractmethod
from typing import Self

from opaque_keys import InvalidKeyError, OpaqueKey
from openedx_keys.impl.base import BackcompatInitMixin, CheckFieldMixin
from openedx_keys.impl.contexts import ContextKey, LibraryKey

__all__ = [
    'ContainerKey',
    'LibraryContainerKey',
]


class ContainerKey(OpaqueKey):  # pylint: disable=abstract-method
    """
    An OpaqueKey identifying a container (unit, section, subsection, etc.).
    Unchanged name.
    """
    KEY_TYPE = 'container_key'
    __slots__ = ()

    @property
    @abstractmethod
    def context_key(self) -> ContextKey:  # pragma: no cover
        """Get the learning context key for this container."""
        raise NotImplementedError()


class LibraryContainerKey(BackcompatInitMixin, CheckFieldMixin, ContainerKey):
    """
    Identifies a container inside a Learning-Core-based library.

    Renamed from LibraryContainerLocator. Old kwarg names
    (container_type, container_id) are accepted with DeprecationWarnings.

    Examples::

        lct:org:lib:unit:my-unit
    """
    CANONICAL_NAMESPACE = 'lct'
    KEY_FIELDS = ('lib_key', 'container_type_code', 'container_code')
    lib_key: LibraryKey
    container_type_code: str
    container_code: str

    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    RENAMED_KWARGS = {
        'container_type': 'container_type_code',
        'container_id': 'container_code',
    }

    CONTAINER_ID_REGEXP = re.compile(r'^[\w\-.]+$', flags=re.UNICODE)

    def __init__(self, lib_key, container_type_code=None, container_code=None, **kwargs):
        """Construct a LibraryContainerKey."""
        # Translate deprecated kwarg aliases at the START, before validation.
        for old, new_name in [('container_type', 'container_type_code'),
                               ('container_id', 'container_code')]:
            if old in kwargs:
                warnings.warn(
                    f"Keyword argument {old!r} is deprecated; use {new_name!r} instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                if new_name == 'container_type_code' and container_type_code is not None:
                    raise TypeError(f"Cannot supply both {old!r} (deprecated) and {new_name!r}")
                if new_name == 'container_code' and container_code is not None:
                    raise TypeError(f"Cannot supply both {old!r} (deprecated) and {new_name!r}")
                if new_name == 'container_type_code':
                    container_type_code = kwargs.pop(old)
                else:
                    container_code = kwargs.pop(old)
        if not isinstance(lib_key, LibraryKey):
            raise TypeError("lib_key must be a LibraryKey")
        self._check_key_string_field("container_type_code", container_type_code)
        self._check_key_string_field(
            "container_code", container_code, regexp=self.CONTAINER_ID_REGEXP
        )
        super().__init__(
            lib_key=lib_key,
            container_type_code=container_type_code,
            container_code=container_code,
        )

    @property
    def container_type(self) -> str:
        """Deprecated. Use container_type_code."""
        warnings.warn(
            "container_type is deprecated; use container_type_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.container_type_code

    @property
    def container_id(self) -> str:
        """Deprecated. Use container_code."""
        warnings.warn(
            "container_id is deprecated; use container_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.container_code

    @property
    def org(self) -> str | None:
        """The organization that this container belongs to."""
        return self.lib_key.org_code

    @property
    def context_key(self) -> LibraryKey:
        """Return the library key."""
        return self.lib_key

    def _to_string(self) -> str:
        """Serialize to a string."""
        return ":".join((
            self.lib_key.org_code,
            self.lib_key.library_code,
            self.container_type_code,
            self.container_code,
        ))

    @classmethod
    def _from_string(cls, serialized: str) -> Self:
        """Deserialize from a string."""
        try:
            org, lib_slug, container_type_code, container_code = serialized.split(':')
            lib_key = LibraryKey(org_code=org, library_code=lib_slug)
            return cls(lib_key, container_type_code, container_code)
        except (ValueError, TypeError) as error:
            raise InvalidKeyError(cls, serialized) from error
