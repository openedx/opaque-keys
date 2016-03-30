"""
;
OpaqueKey abstract classes for edx-platform object types (courses, definitions, usages, and assets).
"""
import json
from abc import abstractmethod, abstractproperty
from six import text_type

from opaque_keys import OpaqueKey


class CourseKey(OpaqueKey):
    """
    An :class:`opaque_keys.OpaqueKey` identifying a particular Course object.
    """
    KEY_TYPE = 'course_key'
    __slots__ = ()

    @abstractproperty
    def org(self):  # pragma: no cover
        """
        The organization that this course belongs to.
        """
        raise NotImplementedError()

    @abstractproperty
    def course(self):  # pragma: no cover
        """
        The name for this course.

        In old-style IDs, it's the "course" in org/course/run
        """
        raise NotImplementedError()

    @abstractproperty
    def run(self):  # pragma: no cover
        """
        The run for this course.

        In old-style IDs, it's the "run" in org/course/run
        """
        raise NotImplementedError()

    @abstractmethod
    def make_usage_key(self, block_type, block_id):  # pragma: no cover
        """
        Return a usage key, given the given the specified block_type and block_id.

        This function should not actually create any new ids, but should simply
        return one that already exists.
        """
        raise NotImplementedError()

    @abstractmethod
    def make_asset_key(self, asset_type, path):  # pragma: no cover
        """
        Return an asset key, given the given the specified path.

        This function should not actually create any new ids, but should simply
        return one that already exists.
        """
        raise NotImplementedError()


class DefinitionKey(OpaqueKey):
    """
    An :class:`opaque_keys.OpaqueKey` identifying an XBlock definition.
    """
    KEY_TYPE = 'definition_key'
    __slots__ = ()

    @abstractproperty
    def block_type(self):  # pragma: no cover
        """
        The XBlock type of this definition.
        """
        raise NotImplementedError()


class CourseObjectMixin(object):
    """
    An abstract :class:`opaque_keys.OpaqueKey` mixin
    for keys that belong to courses.
    """
    __slots__ = ()

    @abstractproperty
    def course_key(self):  # pragma: no cover
        """
        Return the :class:`CourseKey` for the course containing this usage.
        """
        raise NotImplementedError()

    @abstractmethod
    def map_into_course(self, course_key):  # pragma: no cover
        """
        Return a new :class:`UsageKey` or :class:`AssetKey` representing this usage inside the
        course identified by the supplied :class:`CourseKey`. It returns the same type as
        `self`

        Args:
            course_key (:class:`CourseKey`): The course to map this object into.

        Returns:
            A new :class:`CourseObjectMixin` instance.
        """
        raise NotImplementedError()


class AssetKey(CourseObjectMixin, OpaqueKey):
    """
    An :class:`opaque_keys.OpaqueKey` identifying a course asset.
    """
    KEY_TYPE = 'asset_key'
    __slots__ = ()

    @abstractproperty
    def asset_type(self):  # pragma: no cover
        """
        Return what type of asset this is.
        """
        raise NotImplementedError()

    @abstractproperty
    def path(self):  # pragma: no cover
        """
        Return the path for this asset.
        """
        raise NotImplementedError()


class UsageKey(CourseObjectMixin, OpaqueKey):
    """
    An :class:`opaque_keys.OpaqueKey` identifying an XBlock usage.
    """
    KEY_TYPE = 'usage_key'
    __slots__ = ()

    @abstractproperty
    def definition_key(self):  # pragma: no cover
        """
        Return the :class:`DefinitionKey` for the XBlock containing this usage.
        """
        raise NotImplementedError()

    @abstractproperty
    def block_type(self):
        """
        The XBlock type of this usage.
        """
        raise NotImplementedError()

    @abstractproperty
    def block_id(self):
        """
        The name of this usage.
        """
        raise NotImplementedError()


class AsideDefinitionKey(DefinitionKey):
    """
    A definition key for an aside.
    """
    __slots__ = ()

    @abstractproperty
    def definition_key(self):
        """
        Return the DefinitionKey that this aside is decorating.
        """
        raise NotImplementedError()

    @abstractproperty
    def aside_type(self):
        """
        Return the type of this aside.
        """
        raise NotImplementedError()


class AsideUsageKey(UsageKey):
    """
    A usage key for an aside.
    """
    __slots__ = ()

    @abstractproperty
    def usage_key(self):
        """
        Return the UsageKey that this aside is decorating.
        """
        raise NotImplementedError()

    @abstractproperty
    def aside_type(self):
        """
        Return the type of this aside.
        """
        raise NotImplementedError()


# Allow class name to start with a lowercase letter
class i4xEncoder(json.JSONEncoder):  # pylint: disable=invalid-name
    """
    If provided as the cls to json.dumps, will serialize and Locations as i4x strings and other
    keys using the unicode strings.
    """
    def default(self, key):  # pylint: disable=method-hidden
        if isinstance(key, OpaqueKey):
            return text_type(key)
        super(i4xEncoder, self).default(key)


class BlockTypeKey(OpaqueKey):
    """
    A key class that encodes XBlock-family block types, including which family the block
    was loaded from.
    """
    KEY_TYPE = 'block_type'
    __slots__ = ()

    @abstractproperty
    def block_family(self):
        """
        Return the block-family identifier (the entry-point used to load that block
        family).
        """
        raise NotImplementedError()

    @abstractproperty
    def block_type(self):
        """
        Return the block_type of this block (the key in the entry-point to load the block
        with).
        """
        raise NotImplementedError()
