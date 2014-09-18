"""
Defines the :class:`OpaqueKey` class, to be used as the base-class for
implementing pluggable OpaqueKeys.

These keys are designed to provide a limited, forward-evolveable interface to
an application, while concealing the particulars of the serialization
formats, and allowing new serialization formats to be installed transparently.
"""
from abc import ABCMeta, abstractmethod, abstractproperty
from copy import deepcopy
from collections import namedtuple
from functools import total_ordering

from stevedore.enabled import EnabledExtensionManager


class InvalidKeyError(Exception):
    """
    Raised to indicated that a serialized key isn't valid (wasn't able to be parsed
    by any available providers).
    """
    def __init__(self, key_class, serialized):
        super(InvalidKeyError, self).__init__(u'{}: {}'.format(key_class, serialized))


class OpaqueKeyMetaclass(ABCMeta):
    """
    Metaclass for :class:`OpaqueKey`. Sets the default value for the values in ``KEY_FIELDS`` to
    ``None``.
    """
    def __new__(mcs, name, bases, attrs):
        if '__slots__' not in attrs:
            for field in attrs.get('KEY_FIELDS', []):
                attrs.setdefault(field, None)
        return super(OpaqueKeyMetaclass, mcs).__new__(mcs, name, bases, attrs)


PLUGIN_CACHE = {}


@total_ordering
class OpaqueKey(object):
    """
    A base-class for implementing pluggable opaque keys. Individual key subclasses identify
    particular types of resources, without specifying the actual form of the key (or
    its serialization).

    There are two levels of expected subclasses: Key type definitions, and key implementations

    ::

        OpaqueKey
            |
        Key type
            |
        Key implementation

    The key type base class must define the class property ``KEY_TYPE``, which identifies
    which ``entry_point`` namespace the keys implementations should be registered with.

    The KeyImplementation classes must define the following:

    ``CANONICAL_NAMESPACE``
        Identifies the key namespace for the particular key implementation
        (when serializing). Key implementations must be registered using the
        ``CANONICAL_NAMESPACE`` as their entry_point name, but can also be registered
        with other names for backwards compatibility.

    ``KEY_FIELDS``
        A list of attribute names that will be used to establish object
        identity. Key implementation instances will compare equal iff all of
        their ``KEY_FIELDS`` match, and will not compare equal to instances
        of different KeyImplementation classes (even if the ``KEY_FIELDS`` match).
        These fields must be hashable.

    ``_to_string``
        Serialize the key into a unicode object. This should not include the namespace
        prefix (``CANONICAL_NAMESPACE``).

    ``_from_string``
        Construct an instance of this :class:`OpaqueKey` from a unicode object. The namespace
        will already have been parsed.

    OpaqueKeys will not have optional constructor parameters (due to the implementation of
    ``KEY_FIELDS``), by default. However, an implementation class can provide a default,
    as long as it passes that default to a call to ``super().__init__``. If the KeyImplementation
    sets the class attribute ``CHECKED_INIT`` to ``False``, then the :class:`OpaqueKey` base
    class constructor will not validate any of the ``KEY_FIELDS`` arguments, and will instead
    just expect all ``KEY_FIELDS`` to be passed as ``kwargs``.

    :class:`OpaqueKey` objects are immutable.

    Serialization of an :class:`OpaqueKey` is performed by using the :func:`unicode` builtin.
    Deserialization is performed by the :meth:`from_string` method.
    """
    __metaclass__ = OpaqueKeyMetaclass
    __slots__ = ('_initialized', 'deprecated')

    NAMESPACE_SEPARATOR = u':'
    CHECKED_INIT = True
    KEY_FIELDS = ()

    # ============= ABSTRACT METHODS ==============
    @classmethod
    @abstractmethod
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
        raise NotImplementedError()

    @abstractmethod
    def _to_string(self):
        """
        Return a serialization of `self`.

        This serialization should not include the namespace prefix.
        """
        raise NotImplementedError()

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """
        Return an instance of `cls` parsed from its deprecated `serialized` form.

        This will be called only if :meth:`OpaqueKey.from_string` is unable to
        parse a key out of `serialized`, and only if `set_deprecated_fallback` has
        been called to register a fallback class.

        Args:
            cls: The :class:`OpaqueKey` subclass.
            serialized (unicode): A serialized :class:`OpaqueKey`, with namespace already removed.

        Raises:
            InvalidKeyError: Should be raised if `serialized` is not a valid serialized key
                understood by `cls`.
        """
        raise NotImplementedError()

    def _to_deprecated_string(self):
        """
        Return a deprecated serialization of `self`.

        This will be called only if `set_deprecated_fallback` has
        been called to register a fallback class, and the key being
        serialized has the attribute `deprecated=True`.

        This serialization should not include the namespace prefix.
        """
        raise NotImplementedError()

    # ============= SERIALIZATION ==============

    def __unicode__(self):
        """
        Serialize this :class:`OpaqueKey`, in the form ``<CANONICAL_NAMESPACE>:<value of _to_string>``.
        """
        if self.deprecated:
            # no namespace on deprecated
            return self._to_deprecated_string()
        return self.NAMESPACE_SEPARATOR.join([self.CANONICAL_NAMESPACE, self._to_string()])  # pylint: disable=no-member

    @classmethod
    def from_string(cls, serialized):
        """
        Return a :class:`OpaqueKey` object deserialized from
        the `serialized` argument. This object will be an instance
        of a subclass of the `cls` argument.

        Args:
            serialized: A stringified form of a :class:`OpaqueKey`
        """
        if serialized is None:
            raise InvalidKeyError(cls, serialized)

        # pylint: disable=protected-access
        try:
            namespace, rest = cls._separate_namespace(serialized)
            return cls.get_namespace_plugin(namespace)._from_string(rest)
        except InvalidKeyError:
            if hasattr(cls, 'deprecated_fallback'):
                return getattr(cls, 'deprecated_fallback')._from_deprecated_string(serialized)
            raise InvalidKeyError(cls, serialized)

    @classmethod
    def _separate_namespace(cls, serialized):
        """
        Return the namespace from a serialized :class:`OpaqueKey`, and
        the rest of the key.

        Args:
            serialized (unicode): A serialized :class:`OpaqueKey`.

        Raises:
            MissingNamespace: Raised when no namespace can be
                extracted from `serialized`.
        """
        namespace, __, rest = serialized.partition(cls.NAMESPACE_SEPARATOR)

        # If ':' isn't found in the string, then the source string
        # is returned as the first result (i.e. namespace); this happens
        # in the case of a malformed input or a deprecated string.
        if namespace == serialized:
            raise InvalidKeyError(cls, serialized)

        return (namespace, rest)

    @classmethod
    def get_namespace_plugin(cls, namespace):
        """
        Return the registered OpaqueKey subclass of cls for the supplied namespace
        """
        # The cache is stored per-calling-class, rather than per-KEY_TYPE,
        # because we should raise InvalidKeyError if the namespace
        # doesn't specify a subclass of cls
        cache_key = (cls, namespace)
        if cache_key not in PLUGIN_CACHE:
            # Ensure all extensions are loaded. Extensions may modify the deprecated_fallback attribute of the class, so
            # they must be loaded before processing any keys.
            drivers = cls._drivers()

            try:
                PLUGIN_CACHE[cache_key] = drivers[namespace].plugin
            except KeyError:
                # Cache that the namespace doesn't correspond to a known plugin,
                # so that we don't waste time checking every time we hit
                # a particular unknown namespace (like i4x)
                PLUGIN_CACHE[cache_key] = InvalidKeyError(cls, '{}:*'.format(namespace))

        plugin = PLUGIN_CACHE[cache_key]
        if isinstance(plugin, Exception):
            raise plugin
        else:
            return plugin

    @classmethod
    def _drivers(cls):
        """
        Return a driver manager for all key classes that are
        subclasses of `cls`.
        """
        return EnabledExtensionManager(
            cls.KEY_TYPE,  # pylint: disable=no-member
            check_func=lambda extension: issubclass(extension.plugin, cls),
            invoke_on_load=False,
        )

    @classmethod
    def set_deprecated_fallback(cls, fallback):
        """
        Register a deprecated fallback class for this class to revert to.
        """
        if hasattr(cls, 'deprecated_fallback'):
            raise AttributeError("Error: cannot register two fallback classes for {!r}.".format(cls))
        setattr(cls, 'deprecated_fallback', fallback)

    # ============= VALUE SEMANTICS ==============
    def __init__(self, *args, **kwargs):
        # The __init__ expects child classes to implement KEY_FIELDS
        # pylint: disable=no-member

        # a flag used to indicate that this instance was deserialized from the
        # deprecated form and should serialize to the deprecated form
        self.deprecated = kwargs.pop('deprecated', False)

        if self.CHECKED_INIT:
            self._checked_init(*args, **kwargs)
        else:
            self._unchecked_init(**kwargs)
        self._initialized = True

    def _checked_init(self, *args, **kwargs):
        """
        Set all KEY_FIELDS using the contents of args and kwargs, treating
        KEY_FIELDS as the arg order, and validating number and order of args.
        """
        if len(args) + len(kwargs) != len(self.KEY_FIELDS):
            raise TypeError('__init__() takes exactly {} arguments ({} given)'.format(
                len(self.KEY_FIELDS),
                len(args) + len(kwargs)
            ))

        keyed_args = dict(zip(self.KEY_FIELDS, args))
        overlapping_args = keyed_args.viewkeys() & kwargs.viewkeys()
        if overlapping_args:
            raise TypeError('__init__() got multiple values for keyword argument {!r}'.format(overlapping_args[0]))

        keyed_args.update(kwargs)

        for key, value in keyed_args.viewitems():
            if key not in self.KEY_FIELDS:
                raise TypeError('__init__() got an unexpected argument {!r}'.format(key))

        self._unchecked_init(**keyed_args)

    def _unchecked_init(self, **kwargs):
        """
        Set all kwargs as attributes.
        """
        for key, value in kwargs.viewitems():
            if key not in self.KEY_FIELDS:
                continue
            setattr(self, key, value)

    def replace(self, **kwargs):
        """
        Return: a new :class:`OpaqueKey` with ``KEY_FIELDS`` specified in ``kwargs`` replaced
            their corresponding values. Deprecation value is also preserved.

        Subclasses should override this if they have required properties that aren't included in their
        ``KEY_FIELDS``.
        """
        existing_values = {key: getattr(self, key) for key in self.KEY_FIELDS}  # pylint: disable=no-member
        existing_values['deprecated'] = self.deprecated

        if all(value == existing_values[key] for (key, value) in kwargs.iteritems() if key in existing_values):
            return self

        existing_values.update(kwargs)
        return type(self)(**existing_values)

    def __setattr__(self, name, value):
        if getattr(self, '_initialized', False):
            raise AttributeError("Can't set {!r}. OpaqueKeys are immutable.".format(name))

        super(OpaqueKey, self).__setattr__(name, value)

    def __delattr__(self, name):
        raise AttributeError("Can't delete {!r}. OpaqueKeys are immutable.".format(name))

    def __copy__(self):
        """
        Because it's immutable, return itself
        """
        return self

    def __deepcopy__(self, memo):
        """
        Because it's immutable, return itself
        """
        memo[id(self)] = self
        return self

    def __setstate__(self, state_dict):
        # used by pickle to set fields on an unpickled object
        for key in state_dict:
            if key in self.KEY_FIELDS:  # pylint: disable=no-member
                setattr(self, key, state_dict[key])

    def __getstate__(self):
        # used by pickle to get fields on an unpickled object
        pickleable_dict = {}
        for key in self.KEY_FIELDS:  # pylint: disable=no-member
            pickleable_dict[key] = getattr(self, key)
        return pickleable_dict

    @property
    def _key(self):
        """Returns a tuple of key fields"""
        return tuple(getattr(self, field) for field in self.KEY_FIELDS) + (self.CANONICAL_NAMESPACE,)  # pylint: disable=no-member

    def __eq__(self, other):
        return isinstance(other, OpaqueKey) and self._key == other._key  # pylint: disable=protected-access

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        if type(self) != type(other):
            raise TypeError()
        return self._key < other._key  # pylint: disable=protected-access

    def __hash__(self):
        return hash(self._key)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(repr(getattr(self, key)) for key in self.KEY_FIELDS)  # pylint: disable=no-member
        )

    def __len__(self):
        """Return the number of characters in the serialized OpaqueKey"""
        return len(unicode(self))
