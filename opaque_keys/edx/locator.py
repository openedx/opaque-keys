"""
Identifier for course resources.
"""

from __future__ import absolute_import

import inspect
import logging
import re
import warnings
from weakref import WeakValueDictionary
from abc import abstractproperty
from six import string_types, text_type
from six.moves import zip  # pylint: disable=redefined-builtin

from bson.errors import InvalidId
from bson.objectid import ObjectId
from bson.son import SON

from opaque_keys import OpaqueKey, InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey, DefinitionKey, AssetKey

log = logging.getLogger(__name__)


class LocalId(object):
    """
    Class for local ids for non-persisted xblocks (which can have hardcoded block_ids if necessary)
    """
    def __init__(self, block_id=None):
        self.block_id = block_id
        super(LocalId, self).__init__()

    def __str__(self):
        return "localid_{}".format(self.block_id or id(self))


class Locator(OpaqueKey):
    """
    A locator identifies a course resource.

    Locator is an abstract base class: do not instantiate
    """

    BLOCK_TYPE_PREFIX = r"type"
    # Prefix for the version portion of a locator URL, when it is preceded by a course ID
    VERSION_PREFIX = r"version"
    ALLOWED_ID_CHARS = r'[\w\-~.:]'
    DEPRECATED_ALLOWED_ID_CHARS = r'[\w\-~.:%]'

    @abstractproperty
    def version(self):  # pragma: no cover
        """
        Returns the ObjectId referencing this specific location.

        Raises:
            InvalidKeyError: if the instance doesn't have a complete enough specification.
        """
        raise NotImplementedError()

    @classmethod
    def as_object_id(cls, value):
        """
        Attempts to cast value as a bson.objectid.ObjectId.

        Raises:
            ValueError: if casting fails
        """
        try:
            return ObjectId(value)
        except InvalidId:
            raise InvalidKeyError(cls, '"%s" is not a valid version_guid' % value)


# `BlockLocatorBase` is another abstract base class, so don't worry that it doesn't
# provide implementations for _from_string, _to_string, and version.
# pylint: disable=abstract-method
class BlockLocatorBase(Locator):
    """
    Abstract base clase for XBlock locators.

    See subclasses for more detail, particularly `CourseLocator` and `BlockUsageLocator`.
    """
    # Prefix for the branch portion of a locator URL
    BRANCH_PREFIX = r"branch"
    # Prefix for the block portion of a locator URL
    BLOCK_PREFIX = r"block"
    BLOCK_ALLOWED_ID_CHARS = r'[\w\-~.:%]'

    ALLOWED_ID_RE = re.compile(r'^' + Locator.ALLOWED_ID_CHARS + r'+\Z', re.UNICODE)
    DEPRECATED_ALLOWED_ID_RE = re.compile(r'^' + Locator.DEPRECATED_ALLOWED_ID_CHARS + r'+\Z', re.UNICODE)

    URL_RE_SOURCE = r"""
        ((?P<org>{ALLOWED_ID_CHARS}+)\+(?P<course>{ALLOWED_ID_CHARS}+)(\+(?P<run>{ALLOWED_ID_CHARS}+))?{SEP})??
        ({BRANCH_PREFIX}@(?P<branch>{ALLOWED_ID_CHARS}+){SEP})?
        ({VERSION_PREFIX}@(?P<version_guid>[a-f0-9]+){SEP})?
        ({BLOCK_TYPE_PREFIX}@(?P<block_type>{ALLOWED_ID_CHARS}+){SEP})?
        ({BLOCK_PREFIX}@(?P<block_id>{BLOCK_ALLOWED_ID_CHARS}+))?
    """.format(
        ALLOWED_ID_CHARS=Locator.ALLOWED_ID_CHARS,
        BLOCK_ALLOWED_ID_CHARS=BLOCK_ALLOWED_ID_CHARS,
        BRANCH_PREFIX=BRANCH_PREFIX,
        VERSION_PREFIX=Locator.VERSION_PREFIX,
        BLOCK_TYPE_PREFIX=Locator.BLOCK_TYPE_PREFIX,
        BLOCK_PREFIX=BLOCK_PREFIX,
        SEP=r'(\+(?=.)|\Z)',  # Separator: requires a non-trailing '+' or end of string
    )

    URL_RE = re.compile('^' + URL_RE_SOURCE + r'\Z', re.VERBOSE | re.UNICODE)

    @classmethod
    def parse_url(cls, string):  # pylint: disable=redefined-outer-name
        """
        If it can be parsed as a version_guid with no preceding org + offering, returns a dict
        with key 'version_guid' and the value,

        If it can be parsed as a org + offering, returns a dict
        with key 'id' and optional keys 'branch' and 'version_guid'.

        Raises:
            InvalidKeyError: if string cannot be parsed -or- string ends with a newline.
        """
        match = cls.URL_RE.match(string)
        if not match:
            raise InvalidKeyError(cls, string)
        return match.groupdict()


class CourseLocator(BlockLocatorBase, CourseKey):   # pylint: disable=abstract-method
    """
    Examples of valid CourseLocator specifications:
     CourseLocator(version_guid=ObjectId('519665f6223ebd6980884f2b'))
     CourseLocator(org='mit.eecs', course='6.002x', run='T2_2014')
     CourseLocator(org='mit.eecs', course='6002x', run='fall_2014' branch = 'published')
     CourseLocator.from_string('course-v1:version@519665f6223ebd6980884f2b')
     CourseLocator.from_string('course-v1:mit.eecs+6002x')
     CourseLocator.from_string('course-v1:mit.eecs+6002x+branch@published')
     CourseLocator.from_string('course-v1:mit.eecs+6002x+branch@published+version@519665f6223ebd6980884f2b')

    Should have at least a specific org, course, and run with optional 'branch',
    or version_guid (which points to a specific version). Can contain both in which case
    the persistence layer may raise exceptions if the given version != the current such version
    of the course.
    """

    # pylint: disable=no-member

    CANONICAL_NAMESPACE = 'course-v1'
    KEY_FIELDS = ('org', 'course', 'run', 'branch', 'version_guid')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    # A mapping of parsed key fields to CourseLocator objects, for caching.
    # This is shared across all subclasses, so we use the class as part of the
    # keys.
    __parsed_fields_to_keys = WeakValueDictionary()

    # Characters that are forbidden in the deprecated format
    INVALID_CHARS_DEPRECATED = re.compile(r"[^\w.%-]", re.UNICODE)

    def __init__(self, org=None, course=None, run=None, branch=None, version_guid=None, deprecated=False, **kwargs):
        """
        Construct a CourseLocator

        Args:
            version_guid (string or ObjectId): optional unique id for the version
            org, course, run (string): the standard definition. Optional only if version_guid given
            branch (string): the branch such as 'draft', 'published', 'staged', 'beta'
        """
        offering_arg = kwargs.pop('offering', None)
        if offering_arg:
            warnings.warn(
                "offering is deprecated! Use course and run instead.",
                DeprecationWarning,
                stacklevel=2
            )
            course, __, run = offering_arg.partition("/")

        if deprecated:
            for part in (org, course, run):
                self._check_location_part(part, self.INVALID_CHARS_DEPRECATED)

            fields = [org, course]
            # Deprecated style allowed to have None for run and branch, and allowed to have '' for run
            if run:
                fields.append(run)
            if branch is not None:
                fields.append(branch)
            if not all(self.DEPRECATED_ALLOWED_ID_RE.match(field) for field in fields):
                raise InvalidKeyError(self.__class__, fields)

        else:
            if version_guid:
                version_guid = self.as_object_id(version_guid)

            for name, value in [['org', org], ['course', course], ['run', run], ['branch', branch]]:
                if not (value is None or self.ALLOWED_ID_RE.match(value)):
                    raise InvalidKeyError(self.__class__,
                                          u"Special characters not allowed in field {}: '{}'".format(name, value))

        super(CourseLocator, self).__init__(
            org=org,
            course=course,
            run=run,
            branch=branch,
            version_guid=version_guid,
            deprecated=deprecated,
            **kwargs
        )

        if self.deprecated and (self.org is None or self.course is None):
            raise InvalidKeyError(self.__class__, "Deprecated strings must set both org and course.")

        if not self.deprecated and self.version_guid is None and \
                (self.org is None or self.course is None or self.run is None):
            raise InvalidKeyError(self.__class__, "Either version_guid or org, course, and run should be set")

    @classmethod
    def _check_location_part(cls, val, regexp):  # pylint: disable=missing-docstring
        if val is None:
            return
        if not isinstance(val, string_types):
            raise InvalidKeyError(cls, "{!r} is not a string".format(val))
        if regexp.search(val) is not None:
            raise InvalidKeyError(cls, "Invalid characters in {!r}.".format(val))

    @property
    def version(self):
        """
        Deprecated. The ambiguously named field from CourseLocation which code
        expects to find. Equivalent to version_guid.
        """
        warnings.warn(
            "version is no longer supported as a property of Locators. Please use the version_guid property.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.version_guid

    @property
    def offering(self):
        """
        Deprecated. Use course and run independently.
        """
        warnings.warn(
            "Offering is no longer a supported property of Locator. Please use the course and run properties.",
            DeprecationWarning,
            stacklevel=2
        )
        if not self.course and not self.run:
            return None
        elif not self.run and self.course:
            return self.course
        return "/".join([self.course, self.run])

    @classmethod
    def _from_string(cls, serialized):
        """
        Return a CourseLocator parsing the given serialized string
        :param serialized: matches the string to a CourseLocator
        """
        parse = cls.parse_url(serialized)

        if parse['version_guid']:
            parse['version_guid'] = cls.as_object_id(parse['version_guid'])

        parsed_values = tuple(parse.get(key) for key in cls.KEY_FIELDS)

        # Include the class in the cache key so that we don't have collisions
        # with sub-classes.
        cache_key = (cls.__class__, parsed_values)

        # Note that this is very often called from UsageKey._from_string() and
        # fed the serialized ID without the prefix (so no "course-v1:"), but
        # with a lot of extra non-course-locator stuff at the end. That's why we
        # can't just use cls._cache_pool directly with "serialized" and instead
        # have to use parsed_values as a lookup key. The regex parsing of values
        # is only about 1/4th as expensive as CourseLocator construction, and
        # that doesn't count the much higher cost of hash and eq calculations
        # that are avoided by using a shared CourseLocator object.
        if cache_key in cls.__parsed_fields_to_keys:
            return cls.__parsed_fields_to_keys[cache_key]

        # So you would *think* that because we're pulling all the fields in
        # KEY_FIELDS order, it's safe to say::
        #
        #   course_locator = cls(*parsed_values)
        #
        # However, some subclasses override __init__ to take a **kwargs only,
        # and this would break compatibility. Which is a pity, because that
        # would have been faster. :-(
        course_locator = cls(**dict(zip(cls.KEY_FIELDS, parsed_values)))

        # Serialization is safe because this method is not invoked for
        # deprecated keys, and so they're always safe to serialize (deprecated
        # keys can explode because the run is None).
        full_serialized_key = text_type(course_locator)

        # Write to both our parsed fields cache (needed for when we're called
        # directly), as well as the OpaqueKey general _cache_pool (for when
        # we're invoked from OpaqueKey.from_string()).
        cls.__parsed_fields_to_keys[cache_key] = course_locator
        cls._cache_pool[full_serialized_key] = course_locator

        return course_locator

    def html_id(self):
        """
        Return an id which can be used on an html page as an id attr of an html element.

        To make compatible with old Location object functionality. I don't believe this behavior fits at this
        place, but I have no way to override. We should clearly define the purpose and restrictions of this
        (e.g., I'm assuming periods are fine).
        """
        return text_type(self)

    def make_usage_key(self, block_type, block_id):
        return BlockUsageLocator(
            course_key=self,
            block_type=block_type,
            block_id=block_id,
            deprecated=self.deprecated,
        )

    def make_asset_key(self, asset_type, path):
        return AssetLocator(self, asset_type, path, deprecated=self.deprecated)

    def make_usage_key_from_deprecated_string(self, location_url):
        """
        Deprecated mechanism for creating a UsageKey given a CourseKey and a serialized Location.

        NOTE: this prejudicially takes the tag, org, and course from the url not self.

        Raises:
            InvalidKeyError: if the url does not parse
        """
        warnings.warn(
            "make_usage_key_from_deprecated_string is deprecated! Please use make_usage_key",
            DeprecationWarning,
            stacklevel=2
        )
        return BlockUsageLocator.from_string(location_url).replace(run=self.run)

    def version_agnostic(self):
        """
        We don't care if the locator's version is not the current head; so, avoid version conflict
        by reducing info.
        Returns a copy of itself without any version info.

        Raises:
            ValueError: if the block locator has no org & course, run
        """
        # Short circuit what is by far the most common case.
        if self.version_guid is None:
            return self
        return self.replace(version_guid=None)

    def course_agnostic(self):
        """
        We only care about the locator's version not its course.
        Returns a copy of itself without any course info.

        Raises:
            ValueError: if the block locator has no version_guid
        """
        return self.replace(org=None, course=None, run=None, branch=None)

    def for_branch(self, branch):
        """
        Return a new CourseLocator for another branch of the same course (also version agnostic)
        """
        if self.org is None:
            raise InvalidKeyError(self.__class__, "Branches must have full course ids not just versions")

        # Short circuit what is by far the most common case.
        if branch == self.branch and self.version_guid is None:
            return self
        return self.replace(branch=branch, version_guid=None)

    def for_version(self, version_guid):
        """
        Return a new CourseLocator for another version of the same course and branch. Usually used
        when the head is updated (and thus the course x branch now points to this version)
        """
        return self.replace(version_guid=version_guid)

    def _to_string(self):
        """
        Return a string representing this location.
        """
        parts = []
        if self.course and self.run:
            parts.extend([self.org, self.course, self.run])
            if self.branch:
                parts.append(u"{prefix}@{branch}".format(prefix=self.BRANCH_PREFIX, branch=self.branch))
        if self.version_guid:
            parts.append(u"{prefix}@{guid}".format(prefix=self.VERSION_PREFIX, guid=self.version_guid))
        return u"+".join(parts)

    def _to_deprecated_string(self):
        """Returns an 'old-style' course id, represented as 'org/course/run'"""
        return u'/'.join([self.org, self.course, self.run])

    def to_deprecated_string(self):
        """Deprecated. Use unicode(key) instead."""
        warnings.warn(
            "to_deprecated_string is deprecated! Use unicode(key) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return text_type(self)

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
        if serialized.count('/') != 2:
            raise InvalidKeyError(cls, serialized)

        return cls(*serialized.split('/'), deprecated=True)

CourseKey.set_deprecated_fallback(CourseLocator)


class LibraryLocator(BlockLocatorBase, CourseKey):
    """
    Locates a library. Libraries are XBlock structures with a 'library' block
    at their root.

    Libraries are treated analogously to courses for now. Once opaque keys are
    better supported, they will no longer have the 'run' property, and may no
    longer conform to CourseKey but rather some more general key type.

    Examples of valid LibraryLocator specifications:
     LibraryLocator(version_guid=ObjectId('519665f6223ebd6980884f2b'))
     LibraryLocator(org='UniX', library='PhysicsProbs')
     LibraryLocator.from_string('library-v1:UniX+PhysicsProbs')

    version_guid is optional.

    The constructor accepts 'course' as a deprecated alias for the 'library'
    attribute.

    branch is optional.
    """
    CANONICAL_NAMESPACE = 'library-v1'
    RUN = 'library'  # For backwards compatibility, LibraryLocators have a read-only 'run' property equal to this
    KEY_FIELDS = ('org', 'library', 'branch', 'version_guid')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    def __init__(self, org=None, library=None, branch=None, version_guid=None, **kwargs):
        """
        Construct a LibraryLocator

        Args:
            version_guid (string or ObjectId): optional unique id for the version
            org, library: the standard definition. Optional only if version_guid given.
            branch (string): the optional branch such as 'draft', 'published', 'staged', 'beta'
        """
        if 'offering' in kwargs:
            raise ValueError("'offering' is not a valid field for a LibraryLocator.")

        if 'course' in kwargs:
            if library is not None:
                raise ValueError("Cannot specify both 'library' and 'course'")
            warnings.warn(
                "For LibraryLocators, use 'library' instead of 'course'.",
                DeprecationWarning,
                stacklevel=2
            )
            library = kwargs.pop('course')

        run = kwargs.pop('run', self.RUN)
        if run != self.RUN:
            raise ValueError("Invalid run. Should be '{}' or None.".format(self.RUN))

        if version_guid:
            version_guid = self.as_object_id(version_guid)

        for name, value in [['org', org], ['library', library], ['branch', branch]]:
            if not (value is None or self.ALLOWED_ID_RE.match(value)):
                raise InvalidKeyError(self.__class__,
                                      u"Special characters not allowed in field {}: '{}'".format(name, value))

        if kwargs.get('deprecated', False):
            raise InvalidKeyError(self.__class__, 'LibraryLocator cannot have deprecated=True')

        super(LibraryLocator, self).__init__(
            org=org,
            library=library,
            branch=branch,
            version_guid=version_guid,
            **kwargs
        )

        if self.version_guid is None and (self.org is None or self.library is None):  # pylint: disable=no-member
            raise InvalidKeyError(self.__class__, "Either version_guid or org and library should be set")

    @property
    def run(self):
        """
        Deprecated. Return a 'run' for compatibility with CourseLocator.
        """
        warnings.warn("Accessing 'run' on a LibraryLocator is deprecated.", DeprecationWarning, stacklevel=2)
        return self.RUN

    @property
    def course(self):
        """
        Deprecated. Return a 'course' for compatibility with CourseLocator.
        """
        warnings.warn("Accessing 'course' on a LibraryLocator is deprecated.", DeprecationWarning, stacklevel=2)
        return self.library  # pylint: disable=no-member

    @property
    def version(self):
        """
        Deprecated. The ambiguously named field from CourseLocation which code
        expects to find. Equivalent to version_guid.
        """
        warnings.warn(
            "version is no longer supported as a property of Locators. Please use the version_guid property.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.version_guid  # pylint: disable=no-member

    @classmethod
    def _from_string(cls, serialized):
        """
        Return a LibraryLocator parsing the given serialized string
        :param serialized: matches the string to a LibraryLocator
        """
        parse = cls.parse_url(serialized)

        # The regex detects the "library" key part as "course"
        # since we're sharing a regex with CourseLocator
        parse["library"] = parse["course"]
        del parse["course"]

        if parse['version_guid']:
            parse['version_guid'] = cls.as_object_id(parse['version_guid'])

        return cls(**{key: parse.get(key) for key in cls.KEY_FIELDS})

    def html_id(self):
        """
        Return an id which can be used on an html page as an id attr of an html element.
        """
        return text_type(self)

    def make_usage_key(self, block_type, block_id):
        return LibraryUsageLocator(
            library_key=self,
            block_type=block_type,
            block_id=block_id,
        )

    def make_asset_key(self, asset_type, path):
        return AssetLocator(self, asset_type, path, deprecated=False)

    def version_agnostic(self):
        """
        We don't care if the locator's version is not the current head; so, avoid version conflict
        by reducing info.
        Returns a copy of itself without any version info.

        Raises:
            ValueError: if the block locator has no org & course, run
        """
        return self.replace(version_guid=None)

    def course_agnostic(self):
        """
        We only care about the locator's version not its library.
        Returns a copy of itself without any library info.

        Raises:
            ValueError: if the block locator has no version_guid
        """
        return self.replace(org=None, library=None, branch=None)

    def for_branch(self, branch):
        """
        Return a new CourseLocator for another branch of the same library (also version agnostic)
        """
        if self.org is None and branch is not None:
            raise InvalidKeyError(self.__class__, "Branches must have full library ids not just versions")
        return self.replace(branch=branch, version_guid=None)

    def for_version(self, version_guid):
        """
        Return a new LibraryLocator for another version of the same library and branch. Usually used
        when the head is updated (and thus the library x branch now points to this version)
        """
        return self.replace(version_guid=version_guid)

    def _to_string(self):
        """
        Return a string representing this location.
        """
        parts = []
        if self.library:  # pylint: disable=no-member
            parts.extend([self.org, self.course])
            if self.branch:  # pylint: disable=no-member
                parts.append(u"{prefix}@{branch}".format(prefix=self.BRANCH_PREFIX, branch=self.branch))  # pylint: disable=no-member
        if self.version_guid:  # pylint: disable=no-member
            parts.append(u"{prefix}@{guid}".format(prefix=self.VERSION_PREFIX, guid=self.version_guid))  # pylint: disable=no-member
        return u"+".join(parts)

    def _to_deprecated_string(self):
        """ LibraryLocators are never deprecated. """
        raise NotImplementedError

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """ LibraryLocators are never deprecated. """
        raise NotImplementedError


class BlockUsageLocator(BlockLocatorBase, UsageKey):
    """
    Encodes a location.

    Locations address modules (aka blocks) which are definitions situated in a
    course instance. Thus, a Location must identify the course and the occurrence of
    the defined element in the course. Courses can be a version of an offering, the
    current draft head, or the current production version.

    Locators can contain both a version and a org + course + run w/ branch. The split mongo functions
    may raise errors if these conflict w/ the current db state (i.e., the course's branch !=
    the version_guid)

    Locations can express as urls as well as dictionaries. They consist of
        package_identifier: course_guid | version_guid
        block : guid
        branch : string

    BlockUsageLocators also support deprecated Location-style formatting with the following mapping:
    Location(org, course, run, category, name, revision) is represented as a BlockUsageLocator with:
      - course_key = a CourseKey comprised of (org, course, run, branch=revision)
      - block_type = category
      - block_id = name
    """
    CANONICAL_NAMESPACE = 'block-v1'
    KEY_FIELDS = ('course_key', 'block_type', 'block_id')
    CHECKED_INIT = False

    DEPRECATED_TAG = 'i4x'  # to combine Locations with BlockUsageLocators

    # fake out class introspection as this is an attr in this class's instances
    course_key = None
    block_type = None

    DEPRECATED_URL_RE = re.compile("""
        i4x://
        (?P<org>[^/]+)/
        (?P<course>[^/]+)/
        (?P<category>[^/]+)/     # category == block_type
        (?P<name>[^@]+)          # name == block_id
        (@(?P<revision>[^/]+))?  # branch == revision
    """, re.VERBOSE)

    # TODO (cpennington): We should decide whether we want to expand the
    # list of valid characters in a location
    DEPRECATED_INVALID_CHARS = re.compile(r"[^\w.%-]", re.UNICODE)
    # Names are allowed to have colons.
    DEPRECATED_INVALID_CHARS_NAME = re.compile(r"[^\w.:%-]", re.UNICODE)

    # html ids can contain word chars and dashes
    DEPRECATED_INVALID_HTML_CHARS = re.compile(r"[^\w-]", re.UNICODE)

    def __init__(self, course_key, block_type, block_id, **kwargs):
        """
        Construct a BlockUsageLocator
        """
        # Always use the deprecated status of the course key
        deprecated = kwargs['deprecated'] = course_key.deprecated
        block_id = self._parse_block_ref(block_id, deprecated)
        if block_id is None and not deprecated:
            raise InvalidKeyError(self.__class__, "Missing block id")

        super(BlockUsageLocator, self).__init__(course_key=course_key, block_type=block_type, block_id=block_id,
                                                **kwargs)

    def replace(self, **kwargs):
        # BlockUsageLocator allows for the replacement of 'KEY_FIELDS' in 'self.course_key'.
        # This includes the deprecated 'KEY_FIELDS' of CourseLocator `'revision'` and `'version'`.
        course_key_kwargs = {}
        for key in CourseLocator.KEY_FIELDS:
            if key in kwargs:
                course_key_kwargs[key] = kwargs.pop(key)
        if 'revision' in kwargs and 'branch' not in course_key_kwargs:
            course_key_kwargs['branch'] = kwargs.pop('revision')
        if 'version' in kwargs and 'version_guid' not in course_key_kwargs:
            course_key_kwargs['version_guid'] = kwargs.pop('version')
        if len(course_key_kwargs) > 0:
            kwargs['course_key'] = self.course_key.replace(**course_key_kwargs)

        # `'name'` and `'category'` are deprecated `KEY_FIELDS`.
        # Their values are reassigned to the new keys.
        if 'name' in kwargs and 'block_id' not in kwargs:
            kwargs['block_id'] = kwargs.pop('name')
        if 'category' in kwargs and 'block_type' not in kwargs:
            kwargs['block_type'] = kwargs.pop('category')
        return super(BlockUsageLocator, self).replace(**kwargs)

    @classmethod
    def _clean(cls, value, invalid):
        """
        Should only be called on deprecated-style values

        invalid should be a compiled regexp of chars to replace with '_'
        """
        return re.sub('_+', '_', invalid.sub('_', value))

    @classmethod
    def clean(cls, value):
        """
        Should only be called on deprecated-style values

        Return value, made into a form legal for locations
        """
        return cls._clean(value, cls.DEPRECATED_INVALID_CHARS)

    @classmethod
    def clean_keeping_underscores(cls, value):
        """
        Should only be called on deprecated-style values

        Return value, replacing INVALID_CHARS, but not collapsing multiple '_' chars.
        This for cleaning asset names, as the YouTube ID's may have underscores in them, and we need the
        transcript asset name to match. In the future we may want to change the behavior of _clean.
        """
        return cls.DEPRECATED_INVALID_CHARS.sub('_', value)

    @classmethod
    def clean_for_url_name(cls, value):
        """
        Should only be called on deprecated-style values

        Convert value into a format valid for location names (allows colons).
        """
        return cls._clean(value, cls.DEPRECATED_INVALID_CHARS_NAME)

    @classmethod
    def clean_for_html(cls, value):
        """
        Should only be called on deprecated-style values

        Convert a string into a form that's safe for use in html ids, classes, urls, etc.
        Replaces all INVALID_HTML_CHARS with '_', collapses multiple '_' chars
        """
        return cls._clean(value, cls.DEPRECATED_INVALID_HTML_CHARS)

    @classmethod
    def _from_string(cls, serialized):
        """
        Requests CourseLocator to deserialize its part and then adds the local deserialization of block
        """
        # Allow access to _from_string protected method
        course_key = CourseLocator._from_string(serialized)  # pylint: disable=protected-access
        parsed_parts = cls.parse_url(serialized)
        block_id = parsed_parts.get('block_id', None)
        if block_id is None:
            raise InvalidKeyError(cls, serialized)
        return cls(course_key, parsed_parts.get('block_type'), block_id)

    def version_agnostic(self):
        """
        We don't care if the locator's version is not the current head; so, avoid version conflict
        by reducing info.
        Returns a copy of itself without any version info.

        Raises:
            ValueError: if the block locator has no org, course, and run
        """
        return self.replace(course_key=self.course_key.version_agnostic())

    def course_agnostic(self):
        """
        We only care about the locator's version not its course.
        Returns a copy of itself without any course info.

        Raises:
            ValueError if the block locator has no version_guid
        """
        return self.replace(course_key=self.course_key.course_agnostic())

    def for_branch(self, branch):
        """
        Return a UsageLocator for the same block in a different branch of the course.
        """
        return self.replace(course_key=self.course_key.for_branch(branch))

    def for_version(self, version_guid):
        """
        Return a UsageLocator for the same block in a different branch of the course.
        """
        return self.replace(course_key=self.course_key.for_version(version_guid))

    @classmethod
    def _parse_block_ref(cls, block_ref, deprecated=False):
        """
        Given `block_ref`, tries to parse it into a valid block reference.

        Returns `block_ref` if it is valid.

        Raises:
            InvalidKeyError: if `block_ref` is invalid.
        """

        if deprecated and block_ref is None:
            return None

        if isinstance(block_ref, LocalId):
            return block_ref

        is_valid_deprecated = deprecated and cls.DEPRECATED_ALLOWED_ID_RE.match(block_ref)
        is_valid = cls.ALLOWED_ID_RE.match(block_ref)

        if is_valid or is_valid_deprecated:
            return block_ref
        else:
            raise InvalidKeyError(cls, block_ref)

    @property
    def definition_key(self):  # pragma: no cover
        """
        Returns the definition key for this object.
        Undefined for Locators.
        """
        raise NotImplementedError()

    @property
    def org(self):
        """Returns the org for this object's course_key."""
        return self.course_key.org

    @property
    def course(self):
        """Returns the course for this object's course_key."""
        return self.course_key.course

    @property
    def run(self):
        """Returns the run for this object's course_key."""
        return self.course_key.run

    @property
    def offering(self):
        """
        Deprecated. Use course and run independently.
        """
        warnings.warn(
            "Offering is no longer a supported property of Locator. Please use the course and run properties.",
            DeprecationWarning,
            stacklevel=2
        )
        if not self.course and not self.run:
            return None
        elif not self.run and self.course:
            return self.course
        return "/".join([self.course, self.run])

    @property
    def branch(self):
        """Returns the branch for this object's course_key."""
        return self.course_key.branch

    @property
    def version_guid(self):
        """Returns the version guid for this object."""
        return self.course_key.version_guid

    @property
    def version(self):
        """
        Deprecated. The ambiguously named field from CourseLocation which code
        expects to find. Equivalent to version_guid.
        """
        warnings.warn(
            "Version is no longer supported as a property of Locators. Please use the version_guid property.",
            DeprecationWarning,
            stacklevel=2
        )

        # Returns the version guid for this object.
        return self.course_key.version_guid

    @property
    def name(self):
        """
        Deprecated. The ambiguously named field from Location which code
        expects to find. Equivalent to block_id.
        """
        warnings.warn(
            "Name is no longer supported as a property of Locators. Please use the block_id property.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.block_id

    @property
    def category(self):
        """
        Deprecated. The ambiguously named field from Location which code
        expects to find. Equivalent to block_type.
        """
        warnings.warn(
            "Category is no longer supported as a property of Locators. Please use the block_type property.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.block_type

    @property
    def revision(self):
        """
        Deprecated. The ambiguously named field from Location which code
        expects to find. Equivalent to branch.
        """
        warnings.warn(
            "Revision is no longer supported as a property of Locators. Please use the branch property.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.branch

    def is_fully_specified(self):
        """Returns boolean; whether or not this object's course_key is fully specified."""
        return self.course_key.is_fully_specified()

    @classmethod
    def make_relative(cls, course_locator, block_type, block_id):
        """
        Return a new instance which has the given block_id in the given course
        :param course_locator: may be a BlockUsageLocator in the same snapshot
        """
        if hasattr(course_locator, 'course_key'):
            course_locator = course_locator.course_key
        return course_locator.make_usage_key(
            block_type=block_type,
            block_id=block_id
        )

    def map_into_course(self, course_key):
        """
        Return a new instance which has the this block_id in the given course
        :param course_key: a CourseKey object representing the new course to map into
        """
        # This is usually the case, especially in Split courses, where the key
        # already exists on the usage key by default.
        if course_key == self.course_key:
            return self
        return self.replace(course_key=course_key)

    def _to_string(self):
        """
        Return a string representing this location.
        """
        # Allow access to _to_string protected method
        return u"{course_key}+{BLOCK_TYPE_PREFIX}@{block_type}+{BLOCK_PREFIX}@{block_id}".format(
            course_key=self.course_key._to_string(),  # pylint: disable=protected-access
            BLOCK_TYPE_PREFIX=self.BLOCK_TYPE_PREFIX,
            block_type=self.block_type,
            BLOCK_PREFIX=self.BLOCK_PREFIX,
            block_id=self.block_id
        )

    def html_id(self):
        """
        Return an id which can be used on an html page as an id attr of an html element.  It is currently also
        persisted by some clients to identify blocks.

        To make compatible with old Location object functionality. I don't believe this behavior fits at this
        place, but I have no way to override. We should clearly define the purpose and restrictions of this
        (e.g., I'm assuming periods are fine).
        """
        if self.deprecated:
            id_fields = [self.DEPRECATED_TAG, self.org, self.course, self.block_type, self.block_id, self.version_guid]
            id_string = u"-".join([v for v in id_fields if v is not None])
            return self.clean_for_html(id_string)
        else:
            return self.block_id

    def _to_deprecated_string(self):
        """
        Returns an old-style location, represented as:
        i4x://org/course/category/name[@revision]  # Revision is optional
        """
        # pylint: disable=missing-format-attribute
        url = u"{0.DEPRECATED_TAG}://{0.course_key.org}/{0.course_key.course}/{0.block_type}/{0.block_id}".format(self)
        if self.course_key.branch:
            url += u"@{rev}".format(rev=self.course_key.branch)
        return url

    def to_deprecated_string(self):
        """Deprecated. Use unicode(key) instead."""
        warnings.warn(
            "to_deprecated_string is deprecated! Use unicode(key) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return text_type(self)

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
        match = cls.DEPRECATED_URL_RE.match(serialized)
        if match is None:
            raise InvalidKeyError(BlockUsageLocator, serialized)
        groups = match.groupdict()
        course_key = CourseLocator(
            org=groups['org'],
            course=groups['course'],
            run=None,
            branch=groups.get('revision'),
            deprecated=True,
        )
        return cls(course_key, groups['category'], groups['name'], deprecated=True)

    def to_deprecated_son(self, prefix='', tag='i4x'):
        """
        Returns a SON object that represents this location
        """
        # This preserves the old SON keys ('tag', 'org', 'course', 'category', 'name', 'revision'),
        # because that format was used to store data historically in mongo

        # adding tag b/c deprecated form used it
        son = SON({prefix + 'tag': tag})
        for field_name in ('org', 'course'):
            # Temporary filtering of run field because deprecated form left it out
            son[prefix + field_name] = getattr(self.course_key, field_name)
        for (dep_field_name, field_name) in [('category', 'block_type'), ('name', 'block_id')]:
            son[prefix + dep_field_name] = getattr(self, field_name)

        son[prefix + 'revision'] = self.course_key.branch
        return son

    @classmethod
    def _from_deprecated_son(cls, id_dict, run):
        """
        Return the Location decoding this id_dict and run
        """
        course_key = CourseLocator(
            id_dict['org'],
            id_dict['course'],
            run,
            id_dict['revision'],
            deprecated=True,
        )
        return cls(course_key, id_dict['category'], id_dict['name'], deprecated=True)


# register BlockUsageLocator as the deprecated fallback for UsageKey
UsageKey.set_deprecated_fallback(BlockUsageLocator)


class LibraryUsageLocator(BlockUsageLocator):
    """
    Just like BlockUsageLocator, but this points to a block stored in a library,
    not a course.
    """
    CANONICAL_NAMESPACE = 'lib-block-v1'
    KEY_FIELDS = ('library_key', 'block_type', 'block_id')

    # fake out class introspection as this is an attr in this class's instances
    library_key = None
    block_type = None

    def __init__(self, library_key, block_type, block_id, **kwargs):
        """
        Construct a LibraryUsageLocator
        """
        # LibraryUsageLocator is a new type of locator so should never be deprecated.
        if library_key.deprecated or kwargs.get('deprecated', False):
            raise InvalidKeyError(self.__class__, "LibraryUsageLocators are never deprecated.")

        block_id = self._parse_block_ref(block_id, False)

        try:
            if not all(self.ALLOWED_ID_RE.match(val) for val in (block_type, block_id)):
                raise InvalidKeyError(
                    self.__class__,
                    "Invalid block_type or block_id ({!r}, {!r})".format(block_type, block_id)
                )
        except TypeError:
            raise InvalidKeyError(
                self.__class__,
                "Invalid block_type or block_id ({!r}, {!r})".format(block_type, block_id)
            )

        # We skip the BlockUsageLocator init and go to its superclass:
        # pylint: disable=bad-super-call
        super(BlockUsageLocator, self).__init__(library_key=library_key, block_type=block_type, block_id=block_id,
                                                **kwargs)

    def replace(self, **kwargs):
        # BlockUsageLocator allows for the replacement of 'KEY_FIELDS' in 'self.library_key'
        lib_key_kwargs = {}
        for key in LibraryLocator.KEY_FIELDS:
            if key in kwargs:
                lib_key_kwargs[key] = kwargs.pop(key)
        if 'version' in kwargs and 'version_guid' not in lib_key_kwargs:
            lib_key_kwargs['version_guid'] = kwargs.pop('version')
        if len(lib_key_kwargs) > 0:
            kwargs['library_key'] = self.library_key.replace(**lib_key_kwargs)
        if 'course_key' in kwargs:
            kwargs['library_key'] = kwargs.pop('course_key')
        return super(LibraryUsageLocator, self).replace(**kwargs)

    @classmethod
    def _from_string(cls, serialized):
        """
        Requests LibraryLocator to deserialize its part and then adds the local deserialization of block
        """
        # Allow access to _from_string protected method
        library_key = LibraryLocator._from_string(serialized)  # pylint: disable=protected-access
        parsed_parts = LibraryLocator.parse_url(serialized)

        block_id = parsed_parts.get('block_id', None)
        if block_id is None:
            raise InvalidKeyError(cls, serialized)

        block_type = parsed_parts.get('block_type')
        if block_type is None:
            raise InvalidKeyError(cls, serialized)

        return cls(library_key, parsed_parts.get('block_type'), block_id)

    def version_agnostic(self):
        """
        We don't care if the locator's version is not the current head; so, avoid version conflict
        by reducing info.
        Returns a copy of itself without any version info.

        Raises:
            ValueError: if the block locator has no org, course, and run
        """
        return self.replace(library_key=self.library_key.version_agnostic())

    def for_branch(self, branch):
        """
        Return a UsageLocator for the same block in a different branch of the library.
        """
        return self.replace(library_key=self.library_key.for_branch(branch))

    def for_version(self, version_guid):
        """
        Return a UsageLocator for the same block in a different version of the library.
        """
        return self.replace(library_key=self.library_key.for_version(version_guid))

    @property
    def course_key(self):
        """
        To enable compatibility with BlockUsageLocator, we provide a read-only
        course_key property.
        """
        return self.library_key

    @property
    def run(self):
        """Returns the run for this object's library_key."""
        warnings.warn(
            "Run is a deprecated property of LibraryUsageLocators.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.library_key.run

    def _to_deprecated_string(self):
        """ Disable some deprecated methods of our parent class. """
        raise NotImplementedError

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """ Disable some deprecated methods of our parent class. """
        raise NotImplementedError

    def to_deprecated_son(self, prefix='', tag='i4x'):
        """ Disable some deprecated methods of our parent class. """
        raise NotImplementedError

    @classmethod
    def _from_deprecated_son(cls, id_dict, run):
        """ Disable some deprecated methods of our parent class. """
        raise NotImplementedError


class DefinitionLocator(Locator, DefinitionKey):
    """
    Container for how to locate a description (the course-independent content).
    """
    CANONICAL_NAMESPACE = 'def-v1'
    KEY_FIELDS = ('definition_id', 'block_type')
    CHECKED_INIT = False

    # override the abstractproperty
    block_type = None
    definition_id = None

    def __init__(self, block_type, definition_id, deprecated=False):    # pylint: disable=unused-argument
        if isinstance(definition_id, string_types):
            try:
                definition_id = self.as_object_id(definition_id)
            except ValueError:
                raise InvalidKeyError(DefinitionLocator, definition_id)
        super(DefinitionLocator, self).__init__(definition_id=definition_id, block_type=block_type, deprecated=False)

    def _to_string(self):
        """
        Return a string representing this location.
        unicode(self) returns something like this: "519665f6223ebd6980884f2b+type+problem"
        """
        return u"{}+{}@{}".format(text_type(self.definition_id), self.BLOCK_TYPE_PREFIX, self.block_type)

    URL_RE = re.compile(
        r"^(?P<definition_id>[a-f0-9]+)\+{}@(?P<block_type>{ALLOWED_ID_CHARS}+)\Z".format(
            Locator.BLOCK_TYPE_PREFIX, ALLOWED_ID_CHARS=Locator.ALLOWED_ID_CHARS
        ),
        re.VERBOSE | re.UNICODE
    )

    @classmethod
    def _from_string(cls, serialized):
        """
        Return a DefinitionLocator parsing the given serialized string
        :param serialized: matches the string to
        """
        parse = cls.URL_RE.match(serialized)
        if not parse:
            raise InvalidKeyError(cls, serialized)

        parse = parse.groupdict()
        if parse['definition_id']:
            parse['definition_id'] = cls.as_object_id(parse['definition_id'])

        return cls(**{key: parse.get(key) for key in cls.KEY_FIELDS})

    def version(self):
        """
        Returns the ObjectId referencing this specific location.
        """
        return self.definition_id


class VersionTree(object):
    """
    Holds trees of Locators to represent version histories.
    """
    def __init__(self, locator, tree_dict=None):
        """
        :param locator: must be version specific (Course has version_guid or definition had id)
        """
        if not isinstance(locator, Locator) and not inspect.isabstract(locator):
            raise TypeError("locator {} must be a concrete subclass of Locator".format(locator))
        if not locator.version:
            raise ValueError("locator must be version specific (Course has version_guid or definition had id)")
        self.locator = locator
        if tree_dict is None:
            self.children = []
        else:
            self.children = [VersionTree(child, tree_dict)
                             for child in tree_dict.get(locator.version, [])]


class AssetLocator(BlockUsageLocator, AssetKey):    # pylint: disable=abstract-method
    """
    An AssetKey implementation class.
    """
    CANONICAL_NAMESPACE = 'asset-v1'
    DEPRECATED_TAG = 'c4x'
    __slots__ = BlockUsageLocator.KEY_FIELDS

    ASSET_URL_RE = re.compile(r"""
        ^
        /c4x/
        (?P<org>[^/]+)/
        (?P<course>[^/]+)/
        (?P<category>[^/]+)/
        (?P<name>[^@]+)
        (@(?P<revision>[^/]+))?
        \Z
    """, re.VERBOSE)

    ALLOWED_ID_RE = BlockUsageLocator.DEPRECATED_ALLOWED_ID_RE
    # Allow empty asset ids. Used to generate a prefix url
    DEPRECATED_ALLOWED_ID_RE = re.compile(r'^' + Locator.DEPRECATED_ALLOWED_ID_CHARS + r'+\Z', re.UNICODE)

    @property
    def path(self):
        return self.name

    @property
    def asset_type(self):
        return self.block_type

    def replace(self, **kwargs):

        # `'path'` and `'asset_type'` are deprecated `KEY_FIELDS`.
        # Their values are reassigned to the new keys.
        if 'path' in kwargs and 'block_id' not in kwargs:
            kwargs['block_id'] = kwargs.pop('path')
        if 'asset_type' in kwargs and 'block_type' not in kwargs:
            kwargs['block_type'] = kwargs.pop('asset_type')
        return super(AssetLocator, self).replace(**kwargs)

    def _to_deprecated_string(self):
        """
        Returns an old-style location, represented as:

        /c4x/org/course/category/name
        """
        # pylint: disable=missing-format-attribute
        url = u"/{0.DEPRECATED_TAG}/{0.course_key.org}/{0.course_key.course}/{0.block_type}/{0.block_id}".format(self)
        if self.course_key.branch:
            url += u'@{}'.format(self.course_key.branch)
        return url

    def to_deprecated_string(self):
        """Deprecated. Use unicode(key) instead."""
        warnings.warn(
            "to_deprecated_string is deprecated! Use unicode(key) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return text_type(self)

    @property
    def tag(self):
        """Returns the deprecated tag for this Location."""
        return self.DEPRECATED_TAG

    @classmethod
    def _from_deprecated_string(cls, serialized):
        match = cls.ASSET_URL_RE.match(serialized)
        if match is None:
            raise InvalidKeyError(cls, serialized)
        groups = match.groupdict()
        course_key = CourseLocator(
            groups['org'],
            groups['course'],
            None,
            groups.get('revision', None),
            deprecated=True
        )
        return cls(course_key, groups['category'], groups['name'], deprecated=True)

    def to_deprecated_list_repr(self):
        """
        Thumbnail locations are stored as lists [c4x, org, course, thumbnail, path, None] in contentstore.mongo
        That should be the only use of this method, but the method is general enough to provide the pre-opaque
        Location fields as an array in the old order with the tag.
        """
        return ['c4x', self.org, self.course, self.block_type, self.name, None]

# Register AssetLocator as the deprecated fallback for AssetKey
AssetKey.set_deprecated_fallback(AssetLocator)
