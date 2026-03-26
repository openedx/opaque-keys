"""
openedx_keys.impl.contexts — context (learning context) key hierarchy.

Renames from opaque_keys.edx:
  LearningContextKey  -> ContextKey
  CourseKey           -> CourselikeKey
  CourseLocator       -> CourseRunKey
  LibraryLocator      -> LegacyLibraryKey
  LibraryLocatorV2    -> LibraryKey
"""
from __future__ import annotations

import re
import warnings
from abc import abstractmethod
from typing import Self

from bson.errors import InvalidId
from bson.objectid import ObjectId

from opaque_keys import InvalidKeyError, OpaqueKey
from openedx_keys.impl.base import BackcompatInitMixin, CheckFieldMixin

__all__ = [
    'ContextKey',
    'CourselikeKey',
    'CourseRunKey',
    'LegacyLibraryKey',
    'LibraryKey',
]


class ContextKey(OpaqueKey):  # pylint: disable=abstract-method
    """
    An OpaqueKey identifying a learning context (course, library, program, etc.)

    This concept is more generic than "course". A learning context does not
    necessarily have an org, course_code, or run_code.
    """
    KEY_TYPE = 'context_key'
    __slots__ = ()

    # is_course: subclasses should override this to indicate whether or not this
    # key type represents a course.
    is_course = False


class CourselikeKey(ContextKey):  # pylint: disable=abstract-method
    """
    An OpaqueKey identifying a course-like learning context (course or legacy
    library). Renamed from CourseKey.
    """
    __slots__ = ()
    is_course = True

    @property
    @abstractmethod
    def org_code(self) -> str | None:  # pragma: no cover
        """The organisation that this course belongs to."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def course_code(self) -> str | None:  # pragma: no cover
        """The name for this course (the 'course' part of org/course/run)."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def run_code(self) -> str | None:  # pragma: no cover
        """The run for this course (the 'run' part of org/course/run)."""
        raise NotImplementedError()

    @abstractmethod
    def make_usage_key(self, type_code: str, block_code: str):  # pragma: no cover
        """
        Return a usage key for the given type_code and block_code.

        Old kwarg names (block_type, block_id) are accepted with a
        DeprecationWarning.
        """
        raise NotImplementedError()

    @abstractmethod
    def make_asset_key(self, type_code: str, path: str):  # pragma: no cover
        """
        Return an asset key for the given type_code and path.

        Old kwarg name (asset_type) is accepted with a DeprecationWarning.
        """
        raise NotImplementedError()


# ---------------------------------------------------------------------------
# Locator base classes (ported from locator.py)
# ---------------------------------------------------------------------------

class _Locator(OpaqueKey):  # pylint: disable=abstract-method
    """
    Internal base class shared by CourseRunKey and related locator types.
    Provides shared constants and as_object_id helper.
    """
    BLOCK_TYPE_PREFIX = r"type"
    VERSION_PREFIX = r"version"
    ALLOWED_ID_CHARS = r'[\w\-~.:]'
    DEPRECATED_ALLOWED_ID_CHARS = r'[\w\-~.:%]'

    @property
    def version(self):  # pragma: no cover
        """
        Returns the ObjectId referencing this specific location.
        """
        raise NotImplementedError()

    @classmethod
    def as_object_id(cls, value) -> ObjectId:
        """
        Attempts to cast value as a bson.objectid.ObjectId.
        """
        try:
            return ObjectId(value)
        except InvalidId as key_error:
            raise InvalidKeyError(
                cls, f'"{value}" is not a valid version_guid'
            ) from key_error


class _BlockLocatorBase(_Locator):  # pylint: disable=abstract-method
    """
    Abstract base class for XBlock locators. Provides URL parsing helpers.
    """
    BRANCH_PREFIX = r"branch"
    BLOCK_PREFIX = r"block"
    BLOCK_ALLOWED_ID_CHARS = r'[\w\-~.:%]'

    ALLOWED_ID_RE = re.compile(
        r'^' + _Locator.ALLOWED_ID_CHARS + r'+\Z', re.UNICODE
    )
    DEPRECATED_ALLOWED_ID_RE = re.compile(
        r'^' + _Locator.DEPRECATED_ALLOWED_ID_CHARS + r'+\Z', re.UNICODE
    )

    URL_RE_SOURCE = """
        ((?P<org>{ALLOWED_ID_CHARS}+)\\+(?P<course>{ALLOWED_ID_CHARS}+)(\\+(?P<run>{ALLOWED_ID_CHARS}+))?{SEP})??
        ({BRANCH_PREFIX}@(?P<branch>{ALLOWED_ID_CHARS}+){SEP})?
        ({VERSION_PREFIX}@(?P<version_guid>[a-f0-9]+){SEP})?
        ({BLOCK_TYPE_PREFIX}@(?P<block_type>{ALLOWED_ID_CHARS}+){SEP})?
        ({BLOCK_PREFIX}@(?P<block_id>{BLOCK_ALLOWED_ID_CHARS}+))?
    """.format(
        ALLOWED_ID_CHARS=_Locator.ALLOWED_ID_CHARS,
        BLOCK_ALLOWED_ID_CHARS=BLOCK_ALLOWED_ID_CHARS,
        BRANCH_PREFIX=BRANCH_PREFIX,
        VERSION_PREFIX=_Locator.VERSION_PREFIX,
        BLOCK_TYPE_PREFIX=_Locator.BLOCK_TYPE_PREFIX,
        BLOCK_PREFIX=BLOCK_PREFIX,
        SEP=r'(\+(?=.)|\Z)',
    )

    URL_RE = re.compile('^' + URL_RE_SOURCE + r'\Z', re.VERBOSE | re.UNICODE)

    @classmethod
    def parse_url(cls, string: str) -> dict:
        """
        Parse a locator URL string and return a dict of its components.
        """
        match = cls.URL_RE.match(string)
        if not match:
            raise InvalidKeyError(cls, string)
        return match.groupdict()


# ---------------------------------------------------------------------------
# CourseRunKey  (nee CourseLocator)
# ---------------------------------------------------------------------------

class CourseRunKey(BackcompatInitMixin, _BlockLocatorBase, CourselikeKey):
    """
    Identifies a specific course run (org + course_code + run_code).

    Renamed from CourseLocator. Old kwarg names (org, course, run) are
    accepted with DeprecationWarnings.

    Examples::

        CourseRunKey(org_code='mit.eecs', course_code='6.002x', run_code='T2_2014')
        CourseRunKey.from_string('course-v1:mit.eecs+6002x+T2_2014')
    """
    CANONICAL_NAMESPACE = 'course-v1'
    KEY_FIELDS = ('org_code', 'course_code', 'run_code', 'branch', 'version_guid')
    org_code: str | None
    course_code: str | None
    run_code: str | None
    branch: str | None
    version_guid: ObjectId | None

    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    RENAMED_KWARGS = {
        'org': 'org_code',
        'course': 'course_code',
        'run': 'run_code',
    }

    # Characters that are forbidden in the deprecated format
    INVALID_CHARS_DEPRECATED = re.compile(r"[^\w.%-]", re.UNICODE)

    def __init__(
        self,
        org_code: str | None = None,
        course_code: str | None = None,
        run_code: str | None = None,
        branch: str | None = None,
        version_guid=None,
        deprecated: bool = False,
        **kwargs,
    ):
        """
        Construct a CourseRunKey.

        Args:
            org_code, course_code, run_code: the standard fields.
                Optional only if version_guid is given.
            branch: e.g. 'draft', 'published', 'staged', 'beta'
            version_guid: optional unique id for the version
        """
        # Handle old kwarg names via BackcompatInitMixin before we get here,
        # but also handle any remaining old-name kwargs that arrived via **kwargs
        # (they would have been translated already by the mixin).

        offering_arg = kwargs.pop('offering', None)
        if offering_arg:
            warnings.warn(
                "offering is deprecated! Use course_code and run_code instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            course_code, __, run_code = offering_arg.partition("/")

        if deprecated:
            for part in (org_code, course_code, run_code):
                self._check_location_part(part, self.INVALID_CHARS_DEPRECATED)

            fields = [org_code, course_code]
            if run_code:
                fields.append(run_code)
            if branch is not None:
                fields.append(branch)
            if not all(self.DEPRECATED_ALLOWED_ID_RE.match(f) for f in fields):
                raise InvalidKeyError(self.__class__, fields)

        else:
            if version_guid:
                version_guid = self.as_object_id(version_guid)

            for name, value in [
                ['org_code', org_code],
                ['course_code', course_code],
                ['run_code', run_code],
                ['branch', branch],
            ]:
                if not (value is None or self.ALLOWED_ID_RE.match(value)):
                    raise InvalidKeyError(
                        self.__class__,
                        f"Special characters not allowed in field {name}: '{value}'"
                    )

        super().__init__(
            org_code=org_code,
            course_code=course_code,
            run_code=run_code,
            branch=branch,
            version_guid=version_guid,
            deprecated=deprecated,
            **kwargs
        )

        if self.deprecated and (self.org_code is None or self.course_code is None):
            raise InvalidKeyError(
                self.__class__, "Deprecated strings must set both org and course."
            )

        if (
            not self.deprecated
            and self.version_guid is None
            and (
                self.org_code is None
                or self.course_code is None
                or self.run_code is None
            )
        ):
            raise InvalidKeyError(
                self.__class__,
                "Either version_guid or org_code, course_code, and run_code should be set"
            )

    @classmethod
    def _check_location_part(cls, val, regexp):  # pylint: disable=missing-function-docstring
        if val is None:
            return
        if not isinstance(val, str):
            raise InvalidKeyError(cls, f"{val!r} is not a string")
        if regexp.search(val) is not None:
            raise InvalidKeyError(cls, f"Invalid characters in {val!r}.")

    # ---- deprecated field aliases ----

    @property
    def org(self):
        """Deprecated. Use org_code."""
        warnings.warn(
            "org is deprecated; use org_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.org_code

    @property
    def course(self):
        """Deprecated. Use course_code."""
        warnings.warn(
            "course is deprecated; use course_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.course_code

    @property
    def run(self):
        """Deprecated. Use run_code."""
        warnings.warn(
            "run is deprecated; use run_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.run_code

    @property
    def version(self) -> str | None:
        """Deprecated. Use version_guid."""
        warnings.warn(
            "version is no longer supported as a property of Locators. "
            "Please use the version_guid property.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.version_guid

    @property
    def offering(self):
        """Deprecated. Use course_code and run_code independently."""
        warnings.warn(
            "Offering is no longer a supported property of Locator. "
            "Please use the course_code and run_code properties.",
            DeprecationWarning,
            stacklevel=2,
        )
        if not self.course_code and not self.run_code:
            return None
        if not self.run_code and self.course_code:
            return self.course_code
        return "/".join([self.course_code, self.run_code])

    # ---- key operations ----

    def make_usage_key(self, type_code=None, block_code=None, **kwargs):
        """
        Return a CourseRunUsageKey for the given type_code and block_code.

        Old kwarg names (block_type, block_id) are accepted with warnings.
        """
        from openedx_keys.impl.usages import CourseRunUsageKey  # pylint: disable=import-outside-toplevel
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
        return CourseRunUsageKey(
            course_key=self,
            type_code=type_code,
            block_code=block_code,
            deprecated=self.deprecated,
        )

    def make_asset_key(self, type_code=None, path=None, **kwargs):
        """
        Return a CourseRunAssetKey for the given type_code and path.

        Old kwarg name (asset_type) is accepted with a warning.
        """
        from openedx_keys.impl.assets import CourseRunAssetKey  # pylint: disable=import-outside-toplevel
        if 'asset_type' in kwargs and type_code is None:
            warnings.warn(
                "asset_type kwarg is deprecated; use type_code instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            type_code = kwargs.pop('asset_type')
        return CourseRunAssetKey(self, type_code, path, deprecated=self.deprecated)

    def make_usage_key_from_deprecated_string(self, location_url):
        """
        Deprecated mechanism for creating a UsageKey from a Location string.
        """
        warnings.warn(
            "make_usage_key_from_deprecated_string is deprecated! "
            "Please use make_usage_key",
            DeprecationWarning,
            stacklevel=2,
        )
        from openedx_keys.impl.usages import CourseRunUsageKey  # pylint: disable=import-outside-toplevel
        return CourseRunUsageKey.from_string(location_url).replace(
            run_code=self.run_code
        )

    def version_agnostic(self) -> Self:
        """Return a copy without version info."""
        return self.replace(version_guid=None)

    def course_agnostic(self) -> Self:
        """Return a copy without course info (version only)."""
        return self.replace(
            org_code=None, course_code=None, run_code=None, branch=None
        )

    def for_branch(self, branch: str | None) -> Self:
        """Return a new key for another branch (version agnostic)."""
        if self.org_code is None:
            raise InvalidKeyError(
                self.__class__, "Branches must have full course ids not just versions"
            )
        return self.replace(branch=branch, version_guid=None)

    def for_version(self, version_guid: str) -> Self:
        """Return a new key for another version."""
        return self.replace(version_guid=version_guid)

    def is_fully_specified(self):
        """Return True if org_code, course_code, and run_code are all set."""
        return bool(self.org_code and self.course_code and self.run_code)

    def html_id(self):
        """Return an HTML-safe id string."""
        return str(self)

    @classmethod
    def _from_string(cls, serialized):
        """Deserialize from a string."""
        parse = cls.parse_url(serialized)
        if parse['version_guid']:
            parse['version_guid'] = cls.as_object_id(parse['version_guid'])
        # Map the URL regex group names to our KEY_FIELDS
        return cls(
            org_code=parse.get('org'),
            course_code=parse.get('course'),
            run_code=parse.get('run'),
            branch=parse.get('branch'),
            version_guid=parse.get('version_guid'),
        )

    def _to_string(self) -> str:
        """Serialize to a string (without namespace prefix)."""
        parts = []
        if self.course_code and self.run_code:
            parts.extend([self.org_code, self.course_code, self.run_code])
            if self.branch:
                parts.append(f"{self.BRANCH_PREFIX}@{self.branch}")
        if self.version_guid:
            parts.append(f"{self.VERSION_PREFIX}@{self.version_guid}")
        return "+".join(parts)

    def _to_deprecated_string(self) -> str:
        """Return old-style 'org/course/run'."""
        return '/'.join([self.org_code, self.course_code, self.run_code])

    @classmethod
    def _from_deprecated_string(cls, serialized: str) -> Self:
        """Deserialize from deprecated 'org/course/run' format."""
        if serialized.count('/') != 2:
            raise InvalidKeyError(cls, serialized)
        org, course, run = serialized.split('/')
        return cls(org_code=org, course_code=course, run_code=run, deprecated=True)


# Register CourseRunKey as the deprecated fallback for ContextKey.
# CourselikeKey inherits from ContextKey so its fallback is set here too.
ContextKey.set_deprecated_fallback(CourseRunKey)


# ---------------------------------------------------------------------------
# LegacyLibraryKey  (nee LibraryLocator)
# ---------------------------------------------------------------------------

class LegacyLibraryKey(BackcompatInitMixin, _BlockLocatorBase, CourselikeKey):
    """
    Identifies a legacy (v1) modulestore library.

    Renamed from LibraryLocator. Old kwarg names (org, library, branch) are
    accepted with DeprecationWarnings.

    Examples::

        LegacyLibraryKey(org_code='UniX', library_code='PhysicsProbs')
        LegacyLibraryKey.from_string('library-v1:UniX+PhysicsProbs')
    """
    CANONICAL_NAMESPACE = 'library-v1'
    RUN = 'library'  # For backwards compatibility
    KEY_FIELDS = ('org_code', 'library_code', 'branch', 'version_guid')
    org_code: str | None
    library_code: str | None
    branch: str | None
    version_guid: ObjectId | None

    __slots__ = KEY_FIELDS
    CHECKED_INIT = False
    is_course = False  # inherits from CourselikeKey for historical reasons

    RENAMED_KWARGS = {
        'org': 'org_code',
        'library': 'library_code',
    }

    def __init__(
        self,
        org_code: str | None = None,
        library_code: str | None = None,
        branch: str | None = None,
        version_guid=None,
        **kwargs,
    ):
        if 'offering' in kwargs:
            raise ValueError("'offering' is not a valid field for a LegacyLibraryKey.")

        # 'course' is a deprecated alias for 'library_code' (pre-rename)
        if 'course' in kwargs:
            if library_code is not None:
                raise ValueError("Cannot specify both 'library_code' and 'course'")
            warnings.warn(
                "For LegacyLibraryKey, use 'library_code' instead of 'course'.",
                DeprecationWarning,
                stacklevel=2,
            )
            library_code = kwargs.pop('course')

        run = kwargs.pop('run', self.RUN)
        if run != self.RUN:
            raise ValueError(f"Invalid run. Should be '{self.RUN}' or None.")

        if version_guid:
            version_guid = self.as_object_id(version_guid)

        for name, value in [
            ['org_code', org_code],
            ['library_code', library_code],
            ['branch', branch],
        ]:
            if not (value is None or self.ALLOWED_ID_RE.match(value)):
                raise InvalidKeyError(
                    self.__class__,
                    f"Special characters not allowed in field {name}: '{value}'"
                )

        if kwargs.get('deprecated', False):
            raise InvalidKeyError(
                self.__class__, 'LegacyLibraryKey cannot have deprecated=True'
            )

        super().__init__(
            org_code=org_code,
            library_code=library_code,
            branch=branch,
            version_guid=version_guid,
            **kwargs,
        )

        if self.version_guid is None and (
            self.org_code is None or self.library_code is None
        ):
            raise InvalidKeyError(
                self.__class__,
                "Either version_guid or org_code and library_code should be set"
            )

    # ---- deprecated property aliases ----

    @property
    def org(self):
        """Deprecated. Use org_code."""
        warnings.warn(
            "org is deprecated; use org_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.org_code

    @property
    def library(self):
        """Deprecated. Use library_code."""
        warnings.warn(
            "library is deprecated; use library_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.library_code

    @property
    def run(self):
        """Deprecated. Returns the fixed RUN value for compatibility."""
        warnings.warn(
            "Accessing 'run' on a LegacyLibraryKey is deprecated.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.RUN

    @property
    def course(self):
        """Deprecated. Returns library_code for compatibility."""
        warnings.warn(
            "Accessing 'course' on a LegacyLibraryKey is deprecated.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.library_code

    # ---- CourselikeKey abstract property implementations ----

    @property
    def course_code(self) -> str | None:
        """Returns library_code for CourselikeKey compatibility."""
        warnings.warn(
            "course_code is not meaningful on LegacyLibraryKey; use library_code.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.library_code

    @property
    def run_code(self) -> str | None:
        """Returns RUN for CourselikeKey compatibility."""
        warnings.warn(
            "run_code is not meaningful on LegacyLibraryKey; use library_code.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.RUN

    @property
    def version(self):
        """Deprecated. Use version_guid."""
        warnings.warn(
            "version is no longer supported as a property of Locators. "
            "Please use the version_guid property.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.version_guid

    # ---- key operations ----

    def make_usage_key(self, type_code=None, block_code=None, **kwargs):
        """Return a LegacyLibraryUsageKey."""
        from openedx_keys.impl.usages import LegacyLibraryUsageKey  # pylint: disable=import-outside-toplevel
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
        return LegacyLibraryUsageKey(
            library_key=self,
            type_code=type_code,
            block_code=block_code,
        )

    def make_asset_key(self, type_code=None, path=None, **kwargs):
        """Return a CourseRunAssetKey."""
        from openedx_keys.impl.assets import CourseRunAssetKey  # pylint: disable=import-outside-toplevel
        if 'asset_type' in kwargs and type_code is None:
            warnings.warn(
                "asset_type kwarg is deprecated; use type_code instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            type_code = kwargs.pop('asset_type')
        return CourseRunAssetKey(self, type_code, path, deprecated=False)

    def version_agnostic(self):
        """Return a copy without version info."""
        return self.replace(version_guid=None)

    def course_agnostic(self):
        """Return a copy without library info."""
        return self.replace(org_code=None, library_code=None, branch=None)

    def for_branch(self, branch):
        """Return a copy for another branch (version agnostic)."""
        if self.org_code is None and branch is not None:
            raise InvalidKeyError(
                self.__class__,
                "Branches must have full library ids not just versions"
            )
        return self.replace(branch=branch, version_guid=None)

    def for_version(self, version_guid):
        """Return a copy for another version."""
        return self.replace(version_guid=version_guid)

    def is_fully_specified(self):
        """Return True if org_code and library_code are set."""
        return bool(self.org_code and self.library_code)

    def html_id(self):
        """Return an HTML-safe id string."""
        return str(self)

    @classmethod
    def _from_string(cls, serialized):
        """Deserialize from a string."""
        parse = cls.parse_url(serialized)
        # The regex detects library_code as 'course' since we share the regex
        parse["library_code"] = parse["course"]
        del parse["course"]
        if parse['version_guid']:
            parse['version_guid'] = cls.as_object_id(parse['version_guid'])
        return cls(
            org_code=parse.get('org'),
            library_code=parse.get('library_code'),
            branch=parse.get('branch'),
            version_guid=parse.get('version_guid'),
        )

    def _to_string(self):
        """Serialize to a string (without namespace prefix)."""
        parts = []
        if self.library_code:
            parts.extend([self.org_code, self.library_code])
            if self.branch:
                parts.append(f"{self.BRANCH_PREFIX}@{self.branch}")
        if self.version_guid:
            parts.append(f"{self.VERSION_PREFIX}@{self.version_guid}")
        return "+".join(parts)

    def _to_deprecated_string(self):
        """LegacyLibraryKeys are never deprecated."""
        raise NotImplementedError

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """LegacyLibraryKeys are never deprecated."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# LibraryKey  (nee LibraryLocatorV2)
# ---------------------------------------------------------------------------

class LibraryKey(BackcompatInitMixin, CheckFieldMixin, ContextKey):
    """
    Identifies a Learning-Core-based content library.

    Renamed from LibraryLocatorV2. Old kwarg names (org, slug) are accepted
    with DeprecationWarnings; 'slug' maps to 'library_code'.

    Examples::

        LibraryKey(org_code='MITx', library_code='reallyhardproblems')
        LibraryKey.from_string('lib:MITx:reallyhardproblems')
    """
    CANONICAL_NAMESPACE = 'lib'
    KEY_FIELDS = ('org_code', 'library_code')
    org_code: str
    library_code: str

    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    RENAMED_KWARGS = {
        'org': 'org_code',
        'slug': 'library_code',
    }

    # Allow library slugs to contain unicode characters
    SLUG_REGEXP = re.compile(r'^[\w\-.]+$', flags=re.UNICODE)

    def __init__(self, org_code, library_code):
        self._check_key_string_field("org_code", org_code)
        self._check_key_string_field(
            "library_code", library_code, regexp=self.SLUG_REGEXP
        )
        super().__init__(org_code=org_code, library_code=library_code)

    @property
    def org(self):
        """Deprecated. Use org_code."""
        warnings.warn(
            "org is deprecated; use org_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.org_code

    @property
    def slug(self):
        """Deprecated. Use library_code."""
        warnings.warn(
            "slug is deprecated; use library_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.library_code

    def _to_string(self) -> str:
        return ":".join((self.org_code, self.library_code))

    @classmethod
    def _from_string(cls, serialized: str) -> Self:
        try:
            org, slug = serialized.split(':')
            return cls(org_code=org, library_code=slug)
        except (ValueError, TypeError) as error:
            raise InvalidKeyError(cls, serialized) from error

    def for_branch(self, branch: str | None):
        """
        Compatibility helper: accepts for_branch(None) only.
        """
        if branch is not None:
            raise ValueError(
                "Cannot call for_branch on a LibraryKey, except for_branch(None)."
            )
        return self
