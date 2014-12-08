"""
This file provides implementations of :class:`.AsideDefinitionKey` and :class:`.AsideUsageKey`.

:class:`.AsideUsageKeyV1` stores a :class:`.UsageKey` and an `aside_type`, and serializes as
`<usage_key>::<aside_type>`.

Likewise, :class:`.AsideDefinitionKeyV1` stores a :class:`.DefinitionKey` and an `aside_type',
and serializes as `<definition_key>::<aside_type>`.

See :class:`xblock.fields.BlockScope` for a description of what data definitions and usages
describe. The `AsideDefinitionKey` and `AsideUsageKey` allow :class:`xblock.core.XBlockAside`s to
store scoped data alongside the definition and usage of the particular XBlock usage that they're
commenting on.
"""

from opaque_keys.edx.keys import AsideDefinitionKey, AsideUsageKey, DefinitionKey, UsageKey


def _encode(value):
    """
    Encode all '::' substrings in a string (also encodes '$' so that it can
    be used to mark encoded characters). This way we can use :: to separate
    the two halves of an aside key.
    """
    return value.replace('$', '$$').replace('::', '$::')


def _decode(value):
    """
    Decode '::' and '$' characters encoded by `_encode`.
    """
    return value.replace('$::', '::').replace('$$', '$')


class AsideDefinitionKeyV1(AsideDefinitionKey):  # pylint: disable=abstract-method
    """
    A definition key for an aside.
    """
    CANONICAL_NAMESPACE = 'aside-def-v1'
    KEY_FIELDS = ('definition_key', 'aside_type')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    def __init__(self, definition_key, aside_type):
        super(AsideDefinitionKeyV1, self).__init__(definition_key=definition_key, aside_type=aside_type)

    @property
    def block_type(self):
        return self.definition_key.block_type

    @classmethod
    def _from_string(cls, serialized):
        """
        Return an instance of `cls` parsed from its `serialized` form.

        Args:
            cls: The :class:`OpaqueKey` subclass.
            serialized (unicode): A serialized :class:`OpaqueKey`, with namespace already removed.

        Raises:
            InvalidKeyError: Should be raised if `serialized` is not a valid serialized key
                understood by `cls`.
        """
        def_key, __, aside_type = serialized.partition('::')
        return cls(DefinitionKey.from_string(_decode(def_key)), _decode(aside_type))

    def _to_string(self):
        """
        Return a serialization of `self`.

        This serialization should not include the namespace prefix.
        """
        return u'{}::{}'.format(_encode(unicode(self.definition_key)), _encode(unicode(self.aside_type)))


class AsideUsageKeyV1(AsideUsageKey):  # pylint: disable=abstract-method
    """
    A usage key for an aside.
    """
    CANONICAL_NAMESPACE = 'aside-usage-v1'
    KEY_FIELDS = ('usage_key', 'aside_type')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    def __init__(self, usage_key, aside_type):
        super(AsideUsageKeyV1, self).__init__(usage_key=usage_key, aside_type=aside_type)

    @property
    def block_id(self):
        return self.usage_key.block_id

    @property
    def block_type(self):
        return self.usage_key.block_type

    @property
    def definition_key(self):
        return self.usage_key.definition_key

    @classmethod
    def _from_string(cls, serialized):
        """
        Return an instance of `cls` parsed from its `serialized` form.

        Args:
            cls: The :class:`OpaqueKey` subclass.
            serialized (unicode): A serialized :class:`OpaqueKey`, with namespace already removed.

        Raises:
            InvalidKeyError: Should be raised if `serialized` is not a valid serialized key
                understood by `cls`.
        """
        usage_key, __, aside_type = serialized.partition('::')
        return cls(UsageKey.from_string(_decode(usage_key)), _decode(aside_type))

    def _to_string(self):
        """
        Return a serialization of `self`.

        This serialization should not include the namespace prefix.
        """
        return u'{}::{}'.format(_encode(unicode(self.usage_key)), _encode(unicode(self.aside_type)))
