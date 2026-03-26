"""
openedx_keys.impl.collections — collection key hierarchy.

Renames from opaque_keys.edx:
  CollectionKey (abstract, keys.py)  -> absorbed into the concrete class
  LibraryCollectionLocator           -> CollectionKey (concrete)
"""
from __future__ import annotations

import re
import warnings
from typing import Self

from opaque_keys import InvalidKeyError, OpaqueKey
from openedx_keys.impl.base import CheckFieldMixin
from openedx_keys.impl.contexts import LibraryKey

__all__ = [
    'CollectionKey',
]


class CollectionKey(CheckFieldMixin, OpaqueKey):  # pylint: disable=abstract-method
    """
    An OpaqueKey identifying a content collection inside a library.

    Absorbs the old abstract CollectionKey from keys.py. Renamed from
    LibraryCollectionLocator.

    Examples::

        CollectionKey.from_string('lib-collection:org:lib:my-collection')
    """
    KEY_TYPE = 'collection_key'
    CANONICAL_NAMESPACE = 'lib-collection'
    KEY_FIELDS = ('lib_key', 'collection_code')
    lib_key: LibraryKey
    collection_code: str

    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    COLLECTION_ID_REGEXP = re.compile(r'^[\w\-.]+$', flags=re.UNICODE)

    def __init__(self, lib_key, collection_code):
        """Construct a CollectionKey."""
        if not isinstance(lib_key, LibraryKey):
            raise TypeError("lib_key must be a LibraryKey")
        self._check_key_string_field(
            "collection_code", collection_code, regexp=self.COLLECTION_ID_REGEXP
        )
        super().__init__(lib_key=lib_key, collection_code=collection_code)

    @property
    def collection_id(self) -> str:
        """Deprecated. Use collection_code."""
        warnings.warn(
            "collection_id is deprecated; use collection_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.collection_code

    @property
    def org(self) -> str | None:
        """The organization that this collection belongs to."""
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
            self.collection_code,
        ))

    @classmethod
    def _from_string(cls, serialized: str) -> Self:
        """Deserialize from a string."""
        try:
            org, lib_slug, collection_code = serialized.split(':')
            lib_key = LibraryKey(org_code=org, library_code=lib_slug)
            return cls(lib_key, collection_code)
        except (ValueError, TypeError) as error:
            raise InvalidKeyError(cls, serialized) from error
