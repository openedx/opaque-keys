"""
openedx_keys.impl.usages — usage key hierarchy.

Renames / merges from opaque_keys.edx:
  UsageKey             -> UsageKey        (unchanged name)
  UsageKeyV2           -> ContentUsageKey
  Locator              -> CourselikeUsageKey  (merged with BlockLocatorBase)
  BlockLocatorBase     -> CourselikeUsageKey  (merged)
  BlockUsageLocator    -> CourseRunUsageKey
  LibraryUsageLocator  -> LegacyLibraryUsageKey
  LibraryUsageLocatorV2-> LibraryUsageKey
  AsideUsageKey        -> AsideUsageKey   (unchanged name)
  AsideUsageKeyV1/V2   -> unchanged names
"""
from __future__ import annotations

import re
import warnings
from abc import abstractmethod
from typing import Self

from opaque_keys import InvalidKeyError, OpaqueKey
from openedx_keys.impl.base import BackcompatInitMixin, CheckFieldMixin, CourseObjectMixin, LocalId
from openedx_keys.impl.contexts import (
    ContextKey,
    CourselikeKey,
    CourseRunKey,
    LegacyLibraryKey,
    LibraryKey,
    _BlockLocatorBase,
    _Locator,
)

__all__ = [
    'UsageKey',
    'ContentUsageKey',
    'CourselikeUsageKey',
    'CourseRunUsageKey',
    'LegacyLibraryUsageKey',
    'LibraryUsageKey',
    'AsideUsageKey',
    'AsideUsageKeyV1',
    'AsideUsageKeyV2',
]


# ---------------------------------------------------------------------------
# Abstract base classes
# ---------------------------------------------------------------------------

class UsageKey(CourseObjectMixin, OpaqueKey):  # pylint: disable=abstract-method
    """
    An OpaqueKey identifying an XBlock usage. Unchanged name.
    """
    KEY_TYPE = 'usage_key'
    __slots__ = ()

    @property
    @abstractmethod
    def definition_key(self):  # pragma: no cover
        """Return the DefinitionKey for the XBlock containing this usage."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def type_code(self) -> str:
        """The XBlock type of this usage."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def block_code(self) -> str:
        """The name/id of this usage."""
        raise NotImplementedError()

    @property
    def context_key(self) -> ContextKey:
        """Get the learning context key for this XBlock usage."""
        return self.course_key


class ContentUsageKey(UsageKey):  # pylint: disable=abstract-method
    """
    An OpaqueKey identifying an XBlock used in a specific learning context.
    Renamed from UsageKeyV2.

    ContentUsageKey is a subclass of UsageKey; the main differences are:
      * .course_key is deprecated; use .context_key instead.
      * .definition_key is explicitly disabled.
    """
    __slots__ = ()

    @property
    @abstractmethod
    def context_key(self) -> ContextKey:  # pragma: no cover
        """
        Get the learning context key for this XBlock usage.
        """
        raise NotImplementedError()

    @property
    def definition_key(self):
        """
        Not supported for ContentUsageKey subclasses.
        """
        raise AttributeError(
            "Version 2 usage keys do not support direct .definition_key access. "
            "To get the definition key within edxapp, use: "
            "get_learning_context_impl(usage_key).definition_for_usage(usage_key)"
        )

    @property
    def course_key(self) -> CourselikeKey:
        """Deprecated. Use .context_key instead."""
        warnings.warn(
            "Use .context_key instead of .course_key",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.context_key  # type: ignore[return-value]

    def map_into_course(self, course_key) -> Self:
        """Implement map_into_course for API compatibility."""
        if course_key == self.context_key:
            return self
        raise ValueError("Cannot use map_into_course like that with this key type.")


class CourselikeUsageKey(_BlockLocatorBase, UsageKey):  # pylint: disable=abstract-method
    """
    Abstract base for XBlock usage keys in course-like contexts.

    Merges Locator and BlockLocatorBase from the old codebase.
    """
    # Inherit BLOCK_TYPE_PREFIX, VERSION_PREFIX, etc. from _BlockLocatorBase


# ---------------------------------------------------------------------------
# CourseRunUsageKey  (nee BlockUsageLocator)
# ---------------------------------------------------------------------------

class CourseRunUsageKey(BackcompatInitMixin, CourselikeUsageKey):
    """
    Identifies an XBlock usage within a course run.

    Renamed from BlockUsageLocator. Old kwarg names (block_type, block_id)
    are accepted with DeprecationWarnings.
    """
    CANONICAL_NAMESPACE = 'block-v1'
    KEY_FIELDS = ('course_key', 'type_code', 'block_code')
    CHECKED_INIT = False

    DEPRECATED_TAG = 'i4x'

    course_key: CourseRunKey
    type_code: str
    block_code: str

    RENAMED_KWARGS = {
        'block_type': 'type_code',
        'block_id': 'block_code',
    }

    DEPRECATED_URL_RE = re.compile("""
        i4x://
        (?P<org>[^/]+)/
        (?P<course>[^/]+)/
        (?P<category>[^/]+)/     # category == type_code
        (?P<name>[^@]+)          # name == block_code
        (@(?P<revision>[^/]+))?  # branch == revision
        \\Z
    """, re.VERBOSE)

    DEPRECATED_INVALID_CHARS = re.compile(r"[^\w.%-]", re.UNICODE)
    DEPRECATED_INVALID_CHARS_NAME = re.compile(r"[^\w.:%-]", re.UNICODE)
    DEPRECATED_INVALID_HTML_CHARS = re.compile(r"[^\w-]", re.UNICODE)

    def __init__(self, course_key, type_code=None, block_code=None, **kwargs):
        """Construct a CourseRunUsageKey."""
        # Translate deprecated kwarg aliases at the START, before validation.
        for old, new_name in [('block_type', 'type_code'), ('block_id', 'block_code'),
                               ('category', 'type_code'), ('name', 'block_code')]:
            if old in kwargs:
                warnings.warn(
                    f"Keyword argument {old!r} is deprecated; use {new_name!r} instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                if new_name == 'type_code' and type_code is not None:
                    raise TypeError(f"Cannot supply both {old!r} (deprecated) and {new_name!r}")
                if new_name == 'block_code' and block_code is not None:
                    raise TypeError(f"Cannot supply both {old!r} (deprecated) and {new_name!r}")
                if new_name == 'type_code':
                    type_code = kwargs.pop(old)
                else:
                    block_code = kwargs.pop(old)
        # Validate course_key type before accessing .deprecated
        from openedx_keys.impl.contexts import CourselikeKey  # pylint: disable=import-outside-toplevel
        if not isinstance(course_key, CourselikeKey):
            raise TypeError(
                f"course_key must be a CourselikeKey, got {type(course_key)!r}"
            )
        # Always use the deprecated status of the course key
        deprecated = kwargs['deprecated'] = course_key.deprecated
        block_code = self._parse_block_ref(block_code, deprecated)
        if block_code is None and not deprecated:
            raise InvalidKeyError(self.__class__, "Missing block id")
        super().__init__(
            course_key=course_key,
            type_code=type_code,
            block_code=block_code,
            **kwargs,
        )

    def replace(self, **kwargs) -> Self:
        """Replace KEY_FIELDS; also supports replacement via CourseRunKey fields."""
        course_key_kwargs = {}
        for key in CourseRunKey.KEY_FIELDS:
            if key in kwargs:
                course_key_kwargs[key] = kwargs.pop(key)
        # Translate old CourseLocator field names (deprecated) → new KEY_FIELDS
        for old, new_name in [('org', 'org_code'), ('course', 'course_code'), ('run', 'run_code')]:
            if old in kwargs and new_name not in course_key_kwargs:
                course_key_kwargs[new_name] = kwargs.pop(old)
        # Support other old CourseLocator field names in replace()
        if 'revision' in kwargs and 'branch' not in course_key_kwargs:
            course_key_kwargs['branch'] = kwargs.pop('revision')
        if 'version' in kwargs and 'version_guid' not in course_key_kwargs:
            course_key_kwargs['version_guid'] = kwargs.pop('version')
        if course_key_kwargs:
            kwargs['course_key'] = self.course_key.replace(**course_key_kwargs)

        # Deprecated name aliases
        if 'name' in kwargs and 'block_code' not in kwargs:
            kwargs['block_code'] = kwargs.pop('name')
        if 'category' in kwargs and 'type_code' not in kwargs:
            kwargs['type_code'] = kwargs.pop('category')
        # Also handle old field names that may come in
        if 'block_id' in kwargs and 'block_code' not in kwargs:
            kwargs['block_code'] = kwargs.pop('block_id')
        if 'block_type' in kwargs and 'type_code' not in kwargs:
            kwargs['type_code'] = kwargs.pop('block_type')
        return super().replace(**kwargs)

    @classmethod
    def _clean(cls, value, invalid):
        """Should only be called on deprecated-style values."""
        return re.sub('_+', '_', invalid.sub('_', value))

    @classmethod
    def clean(cls, value: str) -> str:
        """Return value cleaned for deprecated-style locations."""
        return cls._clean(value, cls.DEPRECATED_INVALID_CHARS)

    @classmethod
    def clean_keeping_underscores(cls, value: str) -> str:
        """Return value cleaned for deprecated-style locations (keep underscores)."""
        return cls.DEPRECATED_INVALID_CHARS.sub('_', value)

    @classmethod
    def clean_for_url_name(cls, value: str) -> str:
        """Convert value into a format valid for location names (allows colons)."""
        return cls._clean(value, cls.DEPRECATED_INVALID_CHARS_NAME)

    @classmethod
    def clean_for_html(cls, value: str) -> str:
        """Convert a string for safe use in html ids, classes, etc."""
        return cls._clean(value, cls.DEPRECATED_INVALID_HTML_CHARS)

    @classmethod
    def _from_string(cls, serialized: str) -> Self:
        """Deserialize from a string."""
        # Allow access to _from_string protected method
        course_key = CourseRunKey._from_string(serialized)  # pylint: disable=protected-access
        parsed_parts = cls.parse_url(serialized)
        block_code = parsed_parts.get('block_id', None)
        if block_code is None:
            raise InvalidKeyError(cls, serialized)
        return cls(course_key, parsed_parts.get('block_type'), block_code)

    def version_agnostic(self) -> Self:
        """Return a copy without version info."""
        return self.replace(course_key=self.course_key.version_agnostic())

    def course_agnostic(self) -> Self:
        """Return a copy without course info."""
        return self.replace(course_key=self.course_key.course_agnostic())

    def for_branch(self, branch):
        """Return a key for the same block in a different branch."""
        return self.replace(course_key=self.course_key.for_branch(branch))

    def for_version(self, version_guid):
        """Return a key for the same block in a different version."""
        return self.replace(course_key=self.course_key.for_version(version_guid))

    @classmethod
    def _parse_block_ref(cls, block_ref, deprecated=False):
        """Parse and validate block_ref; return it if valid."""
        if deprecated and block_ref is None:
            return None
        if isinstance(block_ref, LocalId):
            return block_ref
        is_valid_deprecated = deprecated and cls.DEPRECATED_ALLOWED_ID_RE.match(block_ref)
        is_valid = cls.ALLOWED_ID_RE.match(block_ref)
        if is_valid or is_valid_deprecated:
            return block_ref
        raise InvalidKeyError(cls, block_ref)

    @property
    def definition_key(self):  # pragma: no cover
        """Returns the definition key. Undefined for Locator-style keys."""
        raise NotImplementedError()

    # ---- deprecated field aliases ----

    @property
    def block_type(self):
        """Deprecated. Use type_code."""
        warnings.warn(
            "block_type is deprecated; use type_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.type_code

    @property
    def block_id(self):
        """Deprecated. Use block_code."""
        warnings.warn(
            "block_id is deprecated; use block_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.block_code

    @property
    def org(self):
        """Returns the org for this object's course_key."""
        return self.course_key.org_code

    @property
    def course(self):
        """Returns the course for this object's course_key."""
        return self.course_key.course_code

    @property
    def run(self):
        """Returns the run for this object's course_key."""
        return self.course_key.run_code

    @property
    def offering(self):
        """Deprecated. Use course and run independently."""
        warnings.warn(
            "Offering is no longer a supported property of Locator. "
            "Please use the course and run properties.",
            DeprecationWarning,
            stacklevel=2,
        )
        if not self.course and not self.run:
            return None
        if not self.run and self.course:
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
        """Deprecated. Use version_guid."""
        warnings.warn(
            "Version is no longer supported as a property of Locators. "
            "Please use the version_guid property.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.course_key.version_guid

    @property
    def name(self):
        """Deprecated. Use block_code."""
        warnings.warn(
            "Name is no longer supported as a property of Locators. "
            "Please use the block_code property.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.block_code

    @property
    def category(self):
        """Deprecated. Use type_code."""
        warnings.warn(
            "Category is no longer supported as a property of Locators. "
            "Please use the type_code property.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.type_code

    @property
    def revision(self):
        """Deprecated. Use branch."""
        warnings.warn(
            "Revision is no longer supported as a property of Locators. "
            "Please use the branch property.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.branch

    def is_fully_specified(self):
        """Return True if the course_key is fully specified."""
        return self.course_key.is_fully_specified()

    @classmethod
    def make_relative(cls, course_locator, type_code=None, block_code=None, **kwargs):
        """
        Return a new instance with the given block in the given course.

        Old kwarg names (block_type, block_id) are accepted with warnings.
        """
        if 'block_type' in kwargs and type_code is None:
            warnings.warn(
                "block_type kwarg is deprecated; use type_code instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            type_code = kwargs.pop('block_type')
        if 'block_id' in kwargs and block_code is None:
            warnings.warn(
                "block_id kwarg is deprecated; use block_code instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            block_code = kwargs.pop('block_id')
        if hasattr(course_locator, 'course_key'):
            course_locator = course_locator.course_key
        return course_locator.make_usage_key(
            type_code=type_code,
            block_code=block_code,
        )

    def map_into_course(self, course_key):
        """Return a new instance with this block in the given course."""
        return self.replace(course_key=course_key)

    def _to_string(self):
        """Serialize to a string (without namespace prefix)."""
        return (
            f"{self.course_key._to_string()}"  # pylint: disable=protected-access
            f"+{self.BLOCK_TYPE_PREFIX}"
            f"@{self.type_code}+{self.BLOCK_PREFIX}@{self.block_code}"
        )

    def html_id(self):
        """Return an HTML-safe id."""
        if self.deprecated:
            id_fields = [
                self.DEPRECATED_TAG,
                self.org,
                self.course,
                self.type_code,
                self.block_code,
                self.version_guid,
            ]
            id_string = "-".join([str(v) for v in id_fields if v is not None])
            return self.clean_for_html(id_string)
        return self.block_code

    def _to_deprecated_string(self):
        """Return old-style i4x:// URL."""
        url = (
            f"{self.DEPRECATED_TAG}://{self.course_key.org_code}"
            f"/{self.course_key.course_code}"
            f"/{self.type_code}/{self.block_code}"
        )
        if self.course_key.branch:
            url += f"@{self.course_key.branch}"
        return url

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """Deserialize from deprecated i4x:// format."""
        match = cls.DEPRECATED_URL_RE.match(serialized)
        if match is None:
            raise InvalidKeyError(CourseRunUsageKey, serialized)
        groups = match.groupdict()
        course_key = CourseRunKey(
            org_code=groups['org'],
            course_code=groups['course'],
            run_code=None,
            branch=groups.get('revision'),
            deprecated=True,
        )
        return cls(course_key, groups['category'], groups['name'], deprecated=True)

    def to_deprecated_son(self, prefix='', tag='i4x'):
        """Return a SON object representing this location."""
        from bson.son import SON  # pylint: disable=import-outside-toplevel
        son = SON({prefix + 'tag': tag})
        for field_name in ('org', 'course'):
            son[prefix + field_name] = getattr(self.course_key, field_name + '_code')
        for dep_name, field_name in [
            ('category', 'type_code'),
            ('name', 'block_code'),
        ]:
            son[prefix + dep_name] = getattr(self, field_name)
        son[prefix + 'revision'] = self.course_key.branch
        return son

    @classmethod
    def _from_deprecated_son(cls, id_dict, run):
        """Return the Location decoding this id_dict and run."""
        course_key = CourseRunKey(
            id_dict['org'],
            id_dict['course'],
            run,
            id_dict['revision'],
            deprecated=True,
        )
        return cls(course_key, id_dict['category'], id_dict['name'], deprecated=True)


# Register CourseRunUsageKey as the deprecated fallback for UsageKey
UsageKey.set_deprecated_fallback(CourseRunUsageKey)


# ---------------------------------------------------------------------------
# LegacyLibraryUsageKey  (nee LibraryUsageLocator)
# ---------------------------------------------------------------------------

class LegacyLibraryUsageKey(CourseRunUsageKey):
    """
    Identifies an XBlock in a legacy (v1) modulestore library.

    Renamed from LibraryUsageLocator.
    """
    CANONICAL_NAMESPACE = 'lib-block-v1'
    KEY_FIELDS = ('library_key', 'type_code', 'block_code')

    library_key: LegacyLibraryKey
    type_code: str

    def __init__(self, library_key, type_code=None, block_code=None, **kwargs):
        """Construct a LegacyLibraryUsageKey."""
        # Translate deprecated kwarg aliases at the START, before validation.
        for old, new_name in [('block_type', 'type_code'), ('block_id', 'block_code'),
                               ('category', 'type_code'), ('name', 'block_code')]:
            if old in kwargs:
                warnings.warn(
                    f"Keyword argument {old!r} is deprecated; use {new_name!r} instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                if new_name == 'type_code' and type_code is not None:
                    raise TypeError(f"Cannot supply both {old!r} (deprecated) and {new_name!r}")
                if new_name == 'block_code' and block_code is not None:
                    raise TypeError(f"Cannot supply both {old!r} (deprecated) and {new_name!r}")
                if new_name == 'type_code':
                    type_code = kwargs.pop(old)
                else:
                    block_code = kwargs.pop(old)
        if library_key.deprecated or kwargs.get('deprecated', False):
            raise InvalidKeyError(
                self.__class__, "LegacyLibraryUsageKeys are never deprecated."
            )

        block_code = self._parse_block_ref(block_code, False)

        try:
            if not all(
                self.ALLOWED_ID_RE.match(val)
                for val in (type_code, block_code)
            ):
                raise InvalidKeyError(
                    self.__class__,
                    f"Invalid type_code or block_code ({type_code!r}, {block_code!r})"
                )
        except TypeError as error:
            raise InvalidKeyError(
                self.__class__,
                f"Invalid type_code or block_code ({type_code!r}, {block_code!r})"
            ) from error

        # Skip CourseRunUsageKey.__init__ and go to its superclass
        super(CourseRunUsageKey, self).__init__(
            library_key=library_key,
            type_code=type_code,
            block_code=block_code,
            **kwargs,
        )

    def replace(self, **kwargs):
        """Replace KEY_FIELDS; also supports replacement via LegacyLibraryKey fields."""
        lib_key_kwargs = {}
        for key in LegacyLibraryKey.KEY_FIELDS:
            if key in kwargs:
                lib_key_kwargs[key] = kwargs.pop(key)
        # Translate old LibraryLocator field names into lib_key_kwargs
        for old, new_name in [('org', 'org_code'), ('library', 'library_code')]:
            if old in kwargs and new_name not in lib_key_kwargs:
                lib_key_kwargs[new_name] = kwargs.pop(old)
        if 'version' in kwargs and 'version_guid' not in lib_key_kwargs:
            lib_key_kwargs['version_guid'] = kwargs.pop('version')
        if lib_key_kwargs:
            kwargs['library_key'] = self.library_key.replace(**lib_key_kwargs)
        if 'course_key' in kwargs:
            kwargs['library_key'] = kwargs.pop('course_key')
        # Handle old field names
        if 'block_id' in kwargs and 'block_code' not in kwargs:
            kwargs['block_code'] = kwargs.pop('block_id')
        if 'block_type' in kwargs and 'type_code' not in kwargs:
            kwargs['type_code'] = kwargs.pop('block_type')
        return super(CourseRunUsageKey, self).replace(**kwargs)

    @classmethod
    def _from_string(cls, serialized):
        """Deserialize from a string."""
        library_key = LegacyLibraryKey._from_string(serialized)  # pylint: disable=protected-access
        parsed_parts = LegacyLibraryKey.parse_url(serialized)

        block_code = parsed_parts.get('block_id', None)
        if block_code is None:
            raise InvalidKeyError(cls, serialized)

        type_code = parsed_parts.get('block_type')
        if type_code is None:
            raise InvalidKeyError(cls, serialized)

        return cls(library_key, parsed_parts.get('block_type'), block_code)

    def version_agnostic(self):
        """Return a copy without version info."""
        return self.replace(library_key=self.library_key.version_agnostic())

    def for_branch(self, branch):
        """Return a key for the same block in a different branch."""
        return self.replace(library_key=self.library_key.for_branch(branch))

    def for_version(self, version_guid):
        """Return a key for the same block in a different version."""
        return self.replace(library_key=self.library_key.for_version(version_guid))

    @property
    def course_key(self):
        """Return library_key for compatibility with CourseRunUsageKey."""
        return self.library_key

    @property
    def run(self):
        """Deprecated. Run is a deprecated property of LegacyLibraryUsageKey."""
        warnings.warn(
            "Run is a deprecated property of LegacyLibraryUsageKeys.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.library_key.RUN

    def _to_deprecated_string(self):
        """Disabled for this key type."""
        raise NotImplementedError

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """Disabled for this key type."""
        raise NotImplementedError

    def to_deprecated_son(self, prefix='', tag='i4x'):
        """Disabled for this key type."""
        raise NotImplementedError

    @classmethod
    def _from_deprecated_son(cls, id_dict, run):
        """Disabled for this key type."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# LibraryUsageKey  (nee LibraryUsageLocatorV2)
# ---------------------------------------------------------------------------

class LibraryUsageKey(BackcompatInitMixin, CheckFieldMixin, ContentUsageKey):
    """
    Identifies an XBlock in a Learning-Core-based content library.

    Renamed from LibraryUsageLocatorV2. Old kwarg names (block_type, usage_id)
    are accepted with DeprecationWarnings.

    Examples::

        lb:MITx:reallyhardproblems:problem:problem1
    """
    CANONICAL_NAMESPACE = 'lb'
    KEY_FIELDS = ('lib_key', 'type_code', 'usage_code')
    lib_key: LibraryKey
    usage_code: str

    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    RENAMED_KWARGS = {
        'block_type': 'type_code',
        'usage_id': 'usage_code',
    }

    USAGE_ID_REGEXP = re.compile(r'^[\w\-.]+$', flags=re.UNICODE)

    def __init__(self, lib_key, type_code=None, usage_code=None, **kwargs):
        """Construct a LibraryUsageKey."""
        # Translate deprecated kwarg aliases at the START, before validation.
        for old, new_name in [('block_type', 'type_code'), ('usage_id', 'usage_code')]:
            if old in kwargs:
                warnings.warn(
                    f"Keyword argument {old!r} is deprecated; use {new_name!r} instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                if new_name == 'type_code' and type_code is not None:
                    raise TypeError(f"Cannot supply both {old!r} (deprecated) and {new_name!r}")
                if new_name == 'usage_code' and usage_code is not None:
                    raise TypeError(f"Cannot supply both {old!r} (deprecated) and {new_name!r}")
                if new_name == 'type_code':
                    type_code = kwargs.pop(old)
                else:
                    usage_code = kwargs.pop(old)
        if not isinstance(lib_key, LibraryKey):
            raise TypeError("lib_key must be a LibraryKey")
        self._check_key_string_field("type_code", type_code)
        self._check_key_string_field(
            "usage_code", usage_code, regexp=self.USAGE_ID_REGEXP
        )
        super().__init__(
            lib_key=lib_key,
            type_code=type_code,
            usage_code=usage_code,
        )

    @property
    def context_key(self) -> LibraryKey:
        """Return the library key."""
        return self.lib_key

    @property
    def block_code(self) -> str:
        """Return usage_code (block_code is an alias for usage_code)."""
        return self.usage_code

    @property
    def block_id(self) -> str:
        """Deprecated. Use usage_code."""
        warnings.warn(
            "block_id is deprecated; use usage_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.usage_code

    @property
    def block_type(self) -> str:
        """Deprecated. Use type_code."""
        warnings.warn(
            "block_type is deprecated; use type_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.type_code

    @property
    def usage_id(self) -> str:
        """Deprecated. Use usage_code."""
        warnings.warn(
            "usage_id is deprecated; use usage_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.usage_code

    @property
    def course_key(self):
        """Deprecated. Use context_key."""
        warnings.warn(
            "Use .context_key instead of .course_key",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.lib_key

    def html_id(self) -> str:
        """Return an HTML-safe id (deprecated)."""
        warnings.warn(".html_id is deprecated", DeprecationWarning, stacklevel=2)
        return str(self)

    def _to_string(self) -> str:
        """Serialize to a string."""
        return ":".join((
            self.lib_key.org_code,
            self.lib_key.library_code,
            self.type_code,
            self.usage_code,
        ))

    @classmethod
    def _from_string(cls, serialized: str) -> Self:
        """Deserialize from a string."""
        try:
            library_org, library_slug, type_code, usage_code = serialized.split(':')
            lib_key = LibraryKey(org_code=library_org, library_code=library_slug)
            return cls(lib_key, type_code=type_code, usage_code=usage_code)
        except (ValueError, TypeError) as error:
            raise InvalidKeyError(cls, serialized) from error


# ---------------------------------------------------------------------------
# Aside usage keys (encoding helpers copied from asides.py)
# ---------------------------------------------------------------------------

def _encode_v1(value):
    """Encode '::' substrings for v1 aside key encoding."""
    return value.replace('$', '$$').replace('::', '$::')


def _decode_v1(value):
    """Decode v1 aside key encoding."""
    decode_colons = value.replace('$::', '::')
    decode_dollars = decode_colons.replace('$$', '$')
    reencoded = _encode_v1(decode_dollars)
    if reencoded != value:
        raise ValueError(
            f'Ambiguous encoded value, {value!r} could have been encoded as {reencoded!r}'
        )
    return decode_dollars


def _join_keys_v1(left, right):
    """Join two keys for v1 encoding."""
    if left.endswith(':') or '::' in left:
        raise ValueError(
            "Can't join a left string ending in ':' or containing '::'"
        )
    return f"{_encode_v1(left)}::{_encode_v1(right)}"


def _split_keys_v1(joined):
    """Split two keys joined by v1 encoding."""
    left, _, right = joined.partition('::')
    return _decode_v1(left), _decode_v1(right)


def _encode_v2(value):
    """Encode ':' substrings for v2 aside key encoding."""
    return value.replace('$', '$$').replace(':', '$:')


def _decode_v2(value):
    """Decode v2 aside key encoding."""
    if re.search(r'(?<!\$):', value):
        raise ValueError("Unescaped ':' in the encoded string")
    decode_colons = value.replace('$:', ':')
    if re.search(r'(?<!\$)(\$\$)*\$([^$]|\Z)', decode_colons):
        raise ValueError("Unescaped '$' in encoded string")
    return decode_colons.replace('$$', '$')


def _join_keys_v2(left, right):
    """Join two keys for v2 encoding."""
    return f"{_encode_v2(left)}::{_encode_v2(right)}"


def _split_keys_v2(joined):
    """Split two keys joined by v2 encoding."""
    left, _, right = joined.rpartition('::')
    return _decode_v2(left), _decode_v2(right)


class AsideUsageKey(UsageKey):  # pylint: disable=abstract-method
    """
    A usage key for an aside. Abstract; unchanged name.
    """
    __slots__ = ()

    @property
    @abstractmethod
    def usage_key(self):  # pragma: no cover
        """Return the UsageKey that this aside is decorating."""
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


class AsideUsageKeyV2(AsideUsageKey):  # pylint: disable=abstract-method
    """
    A usage key for an aside (v2 encoding). Unchanged name.
    """
    CANONICAL_NAMESPACE = 'aside-usage-v2'
    KEY_FIELDS = ('usage_key', 'aside_type_code')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    USAGE_KEY_ATTRS = ('block_code', 'type_code', 'definition_key', 'course_key')

    def __init__(self, usage_key, aside_type_code, deprecated=False):
        super().__init__(
            usage_key=usage_key,
            aside_type_code=aside_type_code,
            deprecated=deprecated,
        )

    @property
    def block_code(self):
        """Return the block_code from the wrapped usage_key."""
        return self.usage_key.block_code

    @property
    def type_code(self):
        """Return the type_code from the wrapped usage_key."""
        return self.usage_key.type_code

    @property
    def block_id(self):
        """Deprecated. Use block_code."""
        warnings.warn(
            "block_id is deprecated; use block_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.usage_key.block_code

    @property
    def block_type(self):
        """Deprecated. Use type_code."""
        warnings.warn(
            "block_type is deprecated; use type_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.usage_key.type_code

    @property
    def definition_key(self):
        """Return the definition_key from the wrapped usage_key."""
        return self.usage_key.definition_key

    @property
    def course_key(self):
        """Return the course_key from the wrapped usage_key."""
        return self.usage_key.course_key

    def map_into_course(self, course_key):
        """Return a new key with the usage_key mapped into the given course."""
        return self.replace(
            usage_key=self.usage_key.map_into_course(course_key)
        )

    def replace(self, **kwargs):
        """Replace KEY_FIELDS; also delegates inner usage_key field replacements."""
        # Translate deprecated field names
        for old, new in [('aside_type', 'aside_type_code'),
                         ('block_id', 'block_code'),
                         ('block_type', 'type_code')]:
            if old in kwargs and new not in kwargs:
                warnings.warn(
                    f"{old!r} is deprecated; use {new!r} instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                kwargs[new] = kwargs.pop(old)
        if 'usage_key' in kwargs:
            for attr in self.USAGE_KEY_ATTRS:
                kwargs.pop(attr, None)
        else:
            kwargs['usage_key'] = self.usage_key.replace(**{
                key: kwargs.pop(key)
                for key in self.USAGE_KEY_ATTRS
                if key in kwargs
            })
        return super().replace(**kwargs)

    @classmethod
    def _from_string(cls, serialized):
        """Deserialize from a string."""
        try:
            usage_key_str, aside_type_code = _split_keys_v2(serialized)
            return cls(UsageKey.from_string(usage_key_str), aside_type_code)
        except ValueError as exc:
            raise InvalidKeyError(cls, exc.args) from exc

    def _to_string(self):
        """Serialize to a string."""
        return _join_keys_v2(str(self.usage_key), str(self.aside_type_code))


class AsideUsageKeyV1(AsideUsageKeyV2):  # pylint: disable=abstract-method
    """
    A usage key for an aside (v1 encoding). Unchanged name.
    """
    CANONICAL_NAMESPACE = 'aside-usage-v1'

    def __init__(self, usage_key, aside_type_code, deprecated=False):
        serialized_usage_key = str(usage_key)
        if '::' in serialized_usage_key or serialized_usage_key.endswith(':'):
            raise ValueError(
                "Usage keys containing '::' or ending with ':' "
                "break the v1 parsing code"
            )
        super().__init__(
            usage_key=usage_key,
            aside_type_code=aside_type_code,
            deprecated=deprecated,
        )

    @classmethod
    def _from_string(cls, serialized):
        """Deserialize from a string."""
        try:
            usage_key_str, aside_type_code = _split_keys_v1(serialized)
            return cls(UsageKey.from_string(usage_key_str), aside_type_code)
        except ValueError as exc:
            raise InvalidKeyError(cls, exc.args) from exc

    def _to_string(self):
        """Serialize to a string."""
        return _join_keys_v1(str(self.usage_key), str(self.aside_type_code))
