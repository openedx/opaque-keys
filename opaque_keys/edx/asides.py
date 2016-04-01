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
from six import text_type

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

    DEFINITION_KEY_FIELDS = ('block_type', )

    def __init__(self, definition_key, aside_type, deprecated=False):
        super(AsideDefinitionKeyV1, self).__init__(definition_key=definition_key, aside_type=aside_type,
                                                   deprecated=deprecated)

    @property
    def block_type(self):
        return self.definition_key.block_type

    def replace(self, **kwargs):
        """
        Return: a new :class:`AsideDefinitionKeyV1` with ``KEY_FIELDS`` specified in ``kwargs`` replaced
            with their corresponding values. Deprecation value is also preserved.
        """
        if 'definition_key' in kwargs:
            for attr in self.DEFINITION_KEY_FIELDS:
                kwargs.pop(attr, None)
        else:
            kwargs['definition_key'] = self.definition_key.replace(**{
                key: kwargs.pop(key)
                for key
                in self.DEFINITION_KEY_FIELDS
                if key in kwargs
            })
        return super(AsideDefinitionKeyV1, self).replace(**kwargs)

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
        return u'{}::{}'.format(_encode(text_type(self.definition_key)), _encode(text_type(self.aside_type)))


class AsideUsageKeyV1(AsideUsageKey):  # pylint: disable=abstract-method
    """
    A usage key for an aside.
    """
    CANONICAL_NAMESPACE = 'aside-usage-v1'
    KEY_FIELDS = ('usage_key', 'aside_type')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    USAGE_KEY_ATTRS = ('block_id', 'block_type', 'definition_key', 'course_key')

    def __init__(self, usage_key, aside_type, deprecated=False):
        super(AsideUsageKeyV1, self).__init__(usage_key=usage_key, aside_type=aside_type, deprecated=deprecated)

    @property
    def block_id(self):
        return self.usage_key.block_id

    @property
    def block_type(self):
        return self.usage_key.block_type

    @property
    def definition_key(self):
        return self.usage_key.definition_key

    @property
    def course_key(self):
        """
        Return the :class:`CourseKey` for the course containing this usage.
        """
        return self.usage_key.course_key

    def map_into_course(self, course_key):
        """
        Return a new :class:`UsageKey` or :class:`AssetKey` representing this usage inside the
        course identified by the supplied :class:`CourseKey`. It returns the same type as
        `self`

        Args:
            course_key (:class:`CourseKey`): The course to map this object into.

        Returns:
            A new :class:`CourseObjectMixin` instance.
        """
        return self.replace(usage_key=self.usage_key.map_into_course(course_key))

    def replace(self, **kwargs):
        """
        Return: a new :class:`AsideUsageKeyV1` with ``KEY_FIELDS`` specified in ``kwargs`` replaced
            with their corresponding values. Deprecation value is also preserved.
        """
        if 'usage_key' in kwargs:
            for attr in self.USAGE_KEY_ATTRS:
                kwargs.pop(attr, None)
        else:
            kwargs['usage_key'] = self.usage_key.replace(**{
                key: kwargs.pop(key)
                for key
                in self.USAGE_KEY_ATTRS
                if key in kwargs
            })
        return super(AsideUsageKeyV1, self).replace(**kwargs)

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
        return u'{}::{}'.format(_encode(text_type(self.usage_key)), _encode(text_type(self.aside_type)))
