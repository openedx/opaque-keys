"""
Test-only OpaqueKey implementations used as plugins for the opaque_keys.testing namespace.

These are registered in setup.py under 'opaque_keys.testing' entry_points so that
OpaqueKey._drivers() can discover them during tests.  They must live in a stable,
importable module — not in test_*.py files, which pytest may load under different
module names depending on sys.path.
"""
import json

from opaque_keys import OpaqueKey, InvalidKeyError

# The following key classes are all test keys, so don't worry that they don't
# provide implementations for: _from_string, _to_string, _from_deprecated_string,
# and/or _to_deprecated_string.
# pylint: disable=abstract-method


class DummyKey(OpaqueKey):
    """
    Key type for testing
    """
    KEY_TYPE = 'opaque_keys.testing'
    __slots__ = ()


class HexKey(DummyKey):
    """
    Key type for testing; _from_string takes hex values
    """
    KEY_FIELDS = ('value',)
    __slots__ = KEY_FIELDS
    CANONICAL_NAMESPACE = 'hex'

    def _to_string(self):
        return hex(self.value)

    @classmethod
    def _from_string(cls, serialized):
        if not serialized.startswith('0x'):
            raise InvalidKeyError(cls, serialized)
        try:
            return cls(int(serialized, 16))
        except (ValueError, TypeError) as error:
            raise InvalidKeyError(cls, serialized) from error


class HexKeyTwoFields(DummyKey):
    """
    Key type for testing; _from_string takes hex values
    """
    KEY_FIELDS = ('value', 'new_value')
    __slots__ = KEY_FIELDS

    def _to_string(self):
        return hex(self.value)  # pylint: disable=no-member

    @classmethod
    def _from_string(cls, serialized):
        raise InvalidKeyError(cls, serialized)


class Base10Key(DummyKey):
    """
    Key type for testing; _from_string takes base 10 values
    """
    KEY_FIELDS = ('value',)
    # Deliberately not using __slots__, to test both cases
    CANONICAL_NAMESPACE = 'base10'

    def _to_string(self):
        return str(self.value)  # pylint: disable=no-member

    @classmethod
    def _from_string(cls, serialized):
        try:
            return cls(int(serialized))
        except (ValueError, TypeError) as error:
            raise InvalidKeyError(cls, serialized) from error


class DictKey(DummyKey):
    """
    Key type for testing; _from_string takes dictionary values
    """
    KEY_FIELDS = ('value',)
    __slots__ = KEY_FIELDS
    CANONICAL_NAMESPACE = 'dict'

    def _to_string(self):
        return json.dumps(self.value)  # pylint: disable=no-member

    @classmethod
    def _from_string(cls, serialized):
        try:
            return cls(json.loads(serialized))
        except (ValueError, TypeError) as error:
            raise InvalidKeyError(cls, serialized) from error

    def __hash__(self):
        # pylint: disable-next=consider-using-generator, no-member
        return hash(type(self)) + sum([hash(elt) for elt in self.value.keys()])
# pylint: enable=abstract-method
