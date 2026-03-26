"""
openedx_keys.impl.definitions — definition key hierarchy.

Renames from opaque_keys.edx:
  DefinitionKey        -> DefinitionKey        (unchanged name)
  DefinitionLocator    -> CourseRunDefinitionKey
  AsideDefinitionKey   -> AsideDefinitionKey   (unchanged name)
  AsideDefinitionKeyV1 -> AsideDefinitionKeyV1 (unchanged name)
  AsideDefinitionKeyV2 -> AsideDefinitionKeyV2 (unchanged name)
"""
from __future__ import annotations

import re
import warnings
from abc import abstractmethod
from typing import Self

from opaque_keys import InvalidKeyError, OpaqueKey
from openedx_keys.impl.base import BackcompatInitMixin
from openedx_keys.impl.contexts import _Locator
from openedx_keys.impl.usages import (
    _decode_v1,
    _decode_v2,
    _encode_v1,
    _encode_v2,
    _join_keys_v1,
    _join_keys_v2,
    _split_keys_v1,
    _split_keys_v2,
)

__all__ = [
    'DefinitionKey',
    'CourseRunDefinitionKey',
    'AsideDefinitionKey',
    'AsideDefinitionKeyV1',
    'AsideDefinitionKeyV2',
]


class DefinitionKey(OpaqueKey):  # pylint: disable=abstract-method
    """
    An OpaqueKey identifying an XBlock definition. Unchanged name.
    """
    KEY_TYPE = 'definition_key'
    __slots__ = ()

    @property
    @abstractmethod
    def type_code(self) -> str:  # pragma: no cover
        """The XBlock type of this definition."""
        raise NotImplementedError()

    @property
    def block_type(self) -> str:
        """Deprecated. Use type_code."""
        warnings.warn(
            "block_type is deprecated; use type_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.type_code


class CourseRunDefinitionKey(_Locator, DefinitionKey):
    """
    Identifies an XBlock definition by type and BSON ObjectId.

    Renamed from DefinitionLocator. definition_id is a BSON ObjectId and
    is NOT renamed (it's not a code/UUID/PK in the OEP-0068 sense).
    type_code renamed from block_type.
    """
    CANONICAL_NAMESPACE = 'def-v1'
    KEY_FIELDS = ('definition_id', 'type_code')
    CHECKED_INIT = False

    type_code: str

    def __init__(
        self,
        type_code: str,
        definition_id,
        deprecated: bool = False,  # pylint: disable=unused-argument
        **kwargs,
    ):
        from bson.objectid import ObjectId  # pylint: disable=import-outside-toplevel
        if isinstance(definition_id, str):
            try:
                definition_id = self.as_object_id(definition_id)
            except ValueError as error:
                raise InvalidKeyError(CourseRunDefinitionKey, definition_id) from error
        super().__init__(
            definition_id=definition_id,
            type_code=type_code,
            deprecated=False,
            **kwargs,
        )

    @property
    def type_code(self) -> str:
        """The XBlock type of this definition."""
        return self.__dict__.get('type_code', None)

    @property
    def block_type(self) -> str:
        """Deprecated. Use type_code."""
        warnings.warn(
            "block_type is deprecated; use type_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.type_code

    def _to_string(self) -> str:
        """Return a string representing this definition key."""
        return f"{self.definition_id!s}+{self.BLOCK_TYPE_PREFIX}@{self.type_code}"

    URL_RE = re.compile(
        fr"^(?P<definition_id>[a-f0-9]+)\+{_Locator.BLOCK_TYPE_PREFIX}"
        fr"@(?P<type_code>{_Locator.ALLOWED_ID_CHARS}+)\Z",
        re.VERBOSE | re.UNICODE,
    )

    @classmethod
    def _from_string(cls, serialized: str) -> Self:
        """Deserialize from a string."""
        parse = cls.URL_RE.match(serialized)
        if not parse:
            raise InvalidKeyError(cls, serialized)
        data = parse.groupdict()
        if data['definition_id']:
            data['definition_id'] = cls.as_object_id(data['definition_id'])
        return cls(
            type_code=data['type_code'],
            definition_id=data['definition_id'],
        )

    @property
    def version(self):
        """Returns the ObjectId referencing this specific location."""
        return self.definition_id


# ---------------------------------------------------------------------------
# AsideDefinitionKey and implementations
# ---------------------------------------------------------------------------

class AsideDefinitionKey(DefinitionKey):  # pylint: disable=abstract-method
    """
    A definition key for an aside. Unchanged name.
    """
    __slots__ = ()

    @property
    @abstractmethod
    def definition_key(self):  # pragma: no cover
        """Return the DefinitionKey that this aside is decorating."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def aside_type_code(self) -> str:  # pragma: no cover
        """Return the type code of this aside."""
        raise NotImplementedError()

    @property
    def aside_type(self) -> str:
        """Deprecated. Use aside_type_code."""
        warnings.warn(
            "aside_type is deprecated; use aside_type_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.aside_type_code


class AsideDefinitionKeyV2(AsideDefinitionKey):  # pylint: disable=abstract-method
    """
    A definition key for an aside (v2 encoding). Unchanged name.
    """
    CANONICAL_NAMESPACE = 'aside-def-v2'
    KEY_FIELDS = ('definition_key', 'aside_type_code')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    DEFINITION_KEY_FIELDS = ('type_code', )

    def __init__(self, definition_key, aside_type_code, deprecated=False):
        super().__init__(
            definition_key=definition_key,
            aside_type_code=aside_type_code,
            deprecated=deprecated,
        )

    @property
    def type_code(self):
        """Return the type_code from the wrapped definition_key."""
        return self.definition_key.type_code

    @property
    def block_type(self):
        """Deprecated. Use type_code."""
        warnings.warn(
            "block_type is deprecated; use type_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.definition_key.type_code

    def replace(self, **kwargs):
        """Replace KEY_FIELDS; also delegates inner definition_key field replacements."""
        if 'definition_key' in kwargs:
            for attr in self.DEFINITION_KEY_FIELDS:
                kwargs.pop(attr, None)
        else:
            kwargs['definition_key'] = self.definition_key.replace(**{
                key: kwargs.pop(key)
                for key in self.DEFINITION_KEY_FIELDS
                if key in kwargs
            })
        return super().replace(**kwargs)

    @classmethod
    def _from_string(cls, serialized):
        """Deserialize from a string."""
        try:
            def_key_str, aside_type_code = _split_keys_v2(serialized)
            return cls(DefinitionKey.from_string(def_key_str), aside_type_code)
        except ValueError as exc:
            raise InvalidKeyError(cls, exc.args) from exc

    def _to_string(self):
        """Serialize to a string."""
        return _join_keys_v2(str(self.definition_key), str(self.aside_type_code))


class AsideDefinitionKeyV1(AsideDefinitionKeyV2):  # pylint: disable=abstract-method
    """
    A definition key for an aside (v1 encoding). Unchanged name.
    """
    CANONICAL_NAMESPACE = 'aside-def-v1'

    def __init__(self, definition_key, aside_type_code, deprecated=False):
        serialized_def_key = str(definition_key)
        if '::' in serialized_def_key or serialized_def_key.endswith(':'):
            raise ValueError(
                "Definition keys containing '::' or ending with ':' "
                "break the v1 parsing code"
            )
        super().__init__(
            definition_key=definition_key,
            aside_type_code=aside_type_code,
            deprecated=deprecated,
        )

    @classmethod
    def _from_string(cls, serialized):
        """Deserialize from a string."""
        try:
            def_key_str, aside_type_code = _split_keys_v1(serialized)
            return cls(DefinitionKey.from_string(def_key_str), aside_type_code)
        except ValueError as exc:
            raise InvalidKeyError(cls, exc.args) from exc

    def _to_string(self):
        """Serialize to a string."""
        return _join_keys_v1(str(self.definition_key), str(self.aside_type_code))
