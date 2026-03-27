"""
openedx_keys.legacy_api — legacy and deprecated key classes.

These classes are either already deprecated or not promoted to the clean API.
New code should not use this module. Existing code can import from here or
from the opaque_keys.edx.* compat shims.

Contents:
  BlockTypeKey, BlockTypeKeyV1, BlockTypeKeyField  (from keys.py / block_types.py)
  LocationKeyField  (already-deprecated alias from django/models.py)
  VersionTree       (deprecated locator utility from locator.py)
  BundleDefinitionLocator  (deprecated definition key from locator.py)
  SlashSeparatedCourseKey, LocationBase, Location, DeprecatedLocation, AssetLocation
    (deprecated location classes from locations.py)
"""
from __future__ import annotations

import re
import warnings
from abc import abstractmethod
from typing import Any
from uuid import UUID

from opaque_keys import InvalidKeyError, OpaqueKey
from openedx_keys.impl.base import CheckFieldMixin
from openedx_keys.impl.assets import CourseRunAssetKey
from openedx_keys.impl.contexts import (
    CourseRunKey,
    _Locator,
)
from openedx_keys.impl.definitions import DefinitionKey
from openedx_keys.impl.usages import CourseRunUsageKey

from openedx_keys.impl.fields import OpaqueKeyField, UsageKeyField


# ---------------------------------------------------------------------------
# BlockTypeKey hierarchy
# ---------------------------------------------------------------------------

class BlockTypeKey(OpaqueKey):
    """
    A key class encoding XBlock family block types.
    Not promoted to the clean API.
    """
    KEY_TYPE = 'block_type'
    __slots__ = ()

    @property
    @abstractmethod
    def block_family(self) -> str:
        """Return the block-family identifier."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def block_type(self) -> str:
        """Return the block type."""
        raise NotImplementedError()


XBLOCK_V1 = 'xblock.v1'
XMODULE_V1 = 'xmodule.v1'


class BlockTypeKeyV1(BlockTypeKey):  # pylint: disable=abstract-method
    """
    A BlockTypeKey that stores block_family and block_type as strings,
    separated by ':'.
    """
    CANONICAL_NAMESPACE = 'block-type-v1'
    KEY_FIELDS = ('block_family', 'block_type')
    __slots__ = KEY_FIELDS
    CHECKED_INIT = False

    def __init__(self, block_family, block_type):
        if ':' in block_family:
            raise InvalidKeyError(self.__class__, "block_family may not contain ':'.")
        if block_family in (XBLOCK_V1, XMODULE_V1):
            block_family = XBLOCK_V1
        super().__init__(
            block_family=block_family,
            block_type=block_type,
            deprecated=block_family == XBLOCK_V1,
        )

    @classmethod
    def _from_string(cls, serialized):
        """Deserialize from a string."""
        if ':' not in serialized:
            raise InvalidKeyError(
                "BlockTypeKeyV1 keys must contain ':' separating the block "
                "family from the block_type.",
                serialized,
            )
        family, __, block_type = serialized.partition(':')
        return cls(family, block_type)

    def _to_string(self):
        """Serialize to a string."""
        return f"{self.block_family}:{self.block_type}"

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """Deserialize from deprecated (no-namespace) form."""
        return cls(XBLOCK_V1, serialized)

    def _to_deprecated_string(self):
        """Serialize to deprecated form."""
        return self.block_type


BlockTypeKey.set_deprecated_fallback(BlockTypeKeyV1)


# ---------------------------------------------------------------------------
# BlockTypeKeyField and LocationKeyField (django fields)
# ---------------------------------------------------------------------------

class BlockTypeKeyField(OpaqueKeyField):
    """
    A django Field that stores a BlockTypeKey object as a string.
    Kept in legacy_api because its KEY_CLASS (BlockTypeKey) is here.
    """
    description = "A BlockTypeKey object, saved to the DB in the form of a string."
    KEY_CLASS = BlockTypeKey
    _pyi_private_set_type: BlockTypeKey | str | None
    _pyi_private_get_type: BlockTypeKey | None


class LocationKeyField(UsageKeyField):
    """
    A django Field that stores a UsageKey as a string.
    Already deprecated alias; use UsageKeyField instead.
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "LocationKeyField is deprecated. Please use UsageKeyField instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


# ---------------------------------------------------------------------------
# VersionTree
# ---------------------------------------------------------------------------

class VersionTree:
    """
    Holds trees of Locators to represent version histories.
    Deprecated; use direct version_guid comparisons instead.
    """
    def __init__(self, locator, tree_dict=None):
        """
        :param locator: must be version specific (Course has version_guid or
            definition had id)
        """
        import inspect  # pylint: disable=import-outside-toplevel
        if not isinstance(locator, _Locator) and not inspect.isabstract(locator):
            raise TypeError(
                f"locator {locator} must be a concrete subclass of Locator"
            )
        version = (
            (hasattr(locator, 'version_guid') and locator.version_guid)
            or (hasattr(locator, 'definition_id') and locator.definition_id)
        )
        if not version:
            raise ValueError(
                "locator must be version specific (Course has version_guid "
                "or definition had id)"
            )
        self.locator = locator
        if tree_dict is None:
            self.children = []
        else:
            self.children = [
                VersionTree(child, tree_dict)
                for child in tree_dict.get(version, [])
            ]


# ---------------------------------------------------------------------------
# BundleDefinitionLocator
# ---------------------------------------------------------------------------

class BundleDefinitionLocator(CheckFieldMixin, DefinitionKey, _Locator):
    """
    DEPRECATED: Definition key for XBlock content stored in Blockstore bundles.

    This key type was deprecated along with Blockstore:
    https://github.com/openedx/public-engineering/issues/238
    """
    KEY_TYPE = 'definition_key'
    CANONICAL_NAMESPACE = 'bundle-olx'
    KEY_FIELDS = ('bundle_uuid', 'block_type', 'olx_path', '_version_or_draft')
    bundle_uuid: UUID
    olx_path: str
    _version_or_draft: int | str

    __slots__ = KEY_FIELDS
    CHECKED_INIT = False
    OLX_PATH_REGEXP = re.compile(r'^[\w\-./]+$', flags=re.UNICODE)

    def __init__(
        self,
        bundle_uuid,
        block_type: str,
        olx_path: str,
        bundle_version: int | None = None,
        draft_name: str | None = None,
        _version_or_draft=None,
    ):
        """Instantiate a new BundleDefinitionLocator."""
        warnings.warn(
            "BundleDefinitionLocator and Blockstore are deprecated!",
            DeprecationWarning,
            stacklevel=2,
        )
        if not isinstance(bundle_uuid, UUID):
            bundle_uuid_str = bundle_uuid
            bundle_uuid = UUID(bundle_uuid_str)
            if bundle_uuid_str != str(bundle_uuid):
                raise InvalidKeyError(
                    self.__class__,
                    "bundle_uuid field got UUID string that's not in standard form"
                )
        self._check_key_string_field("block_type", block_type)
        self._check_key_string_field(
            "olx_path", olx_path, regexp=self.OLX_PATH_REGEXP
        )

        if (
            (bundle_version is not None)
            + (draft_name is not None)
            + (_version_or_draft is not None)
        ) != 1:
            raise ValueError(
                "Exactly one of [bundle_version, draft_name, _version_or_draft] "
                "must be specified"
            )
        if _version_or_draft is not None:
            if not isinstance(_version_or_draft, int):
                self._check_draft_name(_version_or_draft)
        elif draft_name is not None:
            self._check_draft_name(draft_name)
            _version_or_draft = draft_name
        else:
            assert isinstance(bundle_version, int)
            _version_or_draft = bundle_version

        super().__init__(
            bundle_uuid=bundle_uuid,
            block_type=block_type,
            olx_path=olx_path,
            _version_or_draft=_version_or_draft,
        )

    @property
    def type_code(self) -> str:
        """Return block_type as type_code (DefinitionKey abstract property implementation)."""
        return self.block_type

    @property
    def bundle_version(self) -> int | None:
        """Get the Blockstore bundle version number, or None if a draft name."""
        return (
            self._version_or_draft
            if isinstance(self._version_or_draft, int)
            else None
        )

    @property
    def draft_name(self) -> str | None:
        """Get the Blockstore draft name, or None if a bundle version number."""
        return (
            self._version_or_draft
            if not isinstance(self._version_or_draft, int)
            else None
        )

    def _to_string(self) -> str:
        """Serialize to a string."""
        return ":".join((
            str(self.bundle_uuid),
            str(self._version_or_draft),
            self.block_type,
            self.olx_path,
        ))

    @classmethod
    def _from_string(cls, serialized: str):
        """Deserialize from a string."""
        _version_or_draft: int | str
        try:
            bundle_uuid_str, _version_or_draft, block_type, olx_path = (
                serialized.split(':', 3)
            )
        except ValueError as error:
            raise InvalidKeyError(cls, serialized) from error

        if _version_or_draft.isdigit():
            version_string = _version_or_draft
            _version_or_draft = int(version_string)
            if str(_version_or_draft) != version_string:
                raise InvalidKeyError(cls, serialized)

        try:
            return cls(
                bundle_uuid=bundle_uuid_str,
                block_type=block_type,
                olx_path=olx_path,
                _version_or_draft=_version_or_draft,
            )
        except (ValueError, TypeError) as error:
            raise InvalidKeyError(cls, serialized) from error

    @staticmethod
    def _check_draft_name(value):
        """Check that the draft name is unambiguously not a bundle version number."""
        if not isinstance(value, str) or not value:
            raise ValueError("Expected a non-empty string for draft name")
        if value.isdigit():
            raise ValueError(
                "Cannot use an integer draft name as it conflicts with "
                "bundle version numbers"
            )

    @property
    def version(self) -> Any:
        """Returns _version_or_draft for Locator protocol compatibility."""
        return self._version_or_draft


# ---------------------------------------------------------------------------
# Deprecated location classes (from locations.py)
# ---------------------------------------------------------------------------

class i4xEncoder:  # pylint: disable=invalid-name
    """Deprecated. Use openedx_keys.api.i4xEncoder"""

    def __init__(self, *args, **kwargs):
        """Deprecated. Use openedx_keys.api.i4xEncoder"""
        warnings.warn(
            "locations.i4xEncoder.default is deprecated! "
            "Please use openedx_keys.api.i4xEncoder.default",
            DeprecationWarning,
            stacklevel=2,
        )
        from openedx_keys.api import i4xEncoder as real  # pylint: disable=import-outside-toplevel
        self._real = real(*args, **kwargs)


class SlashSeparatedCourseKey(CourseRunKey):
    """Deprecated. Use CourseRunKey."""
    def __init__(self, org, course, run, **kwargs):
        warnings.warn(
            "SlashSeparatedCourseKey is deprecated! Please use CourseRunKey",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(
            org_code=org, course_code=course, run_code=run, deprecated=True, **kwargs
        )

    @classmethod
    def from_string(cls, serialized):
        """Deprecated. Use CourseRunKey.from_string."""
        warnings.warn(
            "SlashSeparatedCourseKey is deprecated! Please use CourseRunKey",
            DeprecationWarning,
            stacklevel=2,
        )
        return CourseRunKey.from_string(serialized)

    def replace(self, **kwargs):
        """Return a new SlashSeparatedCourseKey with specified fields replaced."""
        return SlashSeparatedCourseKey(
            kwargs.pop('org', self.org_code),
            kwargs.pop('course', self.course_code),
            kwargs.pop('run', self.run_code),
            **kwargs,
        )


class LocationBase:
    """Deprecated. Base class for Location and AssetLocation."""

    DEPRECATED_TAG: str | None = None

    @classmethod
    def _deprecation_warning(cls):
        """Display a deprecation warning for the given cls."""
        if issubclass(cls, Location):
            warnings.warn(
                "Location is deprecated! Please use CourseRunUsageKey",
                DeprecationWarning,
                stacklevel=3,
            )
        elif issubclass(cls, AssetLocation):
            warnings.warn(
                "AssetLocation is deprecated! Please use CourseRunAssetKey",
                DeprecationWarning,
                stacklevel=3,
            )
        else:
            warnings.warn(
                f"{cls} is deprecated!",
                DeprecationWarning,
                stacklevel=3,
            )

    @property
    def tag(self):
        """Deprecated. Returns the deprecated tag for this Location."""
        warnings.warn(
            "Tag is no longer supported as a property of Locators.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.DEPRECATED_TAG

    @classmethod
    def _check_location_part(cls, val, regexp):
        """Deprecated. See CourseRunKey._check_location_part."""
        cls._deprecation_warning()
        return CourseRunKey._check_location_part(val, regexp)  # pylint: disable=protected-access

    @classmethod
    def _clean(cls, value, invalid):
        """Deprecated. See CourseRunUsageKey._clean."""
        cls._deprecation_warning()
        return CourseRunUsageKey._clean(value, invalid)  # pylint: disable=protected-access

    @classmethod
    def clean(cls, value):
        """Deprecated. See CourseRunUsageKey.clean."""
        cls._deprecation_warning()
        return CourseRunUsageKey.clean(value)

    @classmethod
    def clean_keeping_underscores(cls, value):
        """Deprecated. See CourseRunUsageKey.clean_keeping_underscores."""
        cls._deprecation_warning()
        return CourseRunUsageKey.clean_keeping_underscores(value)

    @classmethod
    def clean_for_url_name(cls, value):
        """Deprecated. See CourseRunUsageKey.clean_for_url_name."""
        cls._deprecation_warning()
        return CourseRunUsageKey.clean_for_url_name(value)

    @classmethod
    def clean_for_html(cls, value):
        """Deprecated. See CourseRunUsageKey.clean_for_html."""
        cls._deprecation_warning()
        return CourseRunUsageKey.clean_for_html(value)

    def __init__(self, org, course, run, category, name, revision=None, **kwargs):
        self._deprecation_warning()
        course_key = kwargs.pop('course_key', CourseRunKey(
            org_code=org,
            course_code=course,
            run_code=run,
            branch=revision,
            deprecated=True,
        ))
        super().__init__(course_key, category, name, deprecated=True, **kwargs)

    @classmethod
    def from_string(cls, serialized):
        """Deprecated. Use CourseRunUsageKey.from_string."""
        cls._deprecation_warning()
        return CourseRunUsageKey.from_string(serialized)

    @classmethod
    def _from_deprecated_son(cls, id_dict, run):
        """Deprecated. See CourseRunUsageKey._from_deprecated_son."""
        cls._deprecation_warning()
        return CourseRunUsageKey._from_deprecated_son(id_dict, run)  # pylint: disable=protected-access


class Location(LocationBase, CourseRunUsageKey):  # pylint: disable=abstract-method
    """Deprecated. Use CourseRunUsageKey."""

    DEPRECATED_TAG = 'i4x'

    def replace(self, **kwargs):
        """Return a new Location with specified fields replaced."""
        return Location(
            kwargs.pop('org', self.course_key.org_code),
            kwargs.pop('course', self.course_key.course_code),
            kwargs.pop('run', self.course_key.run_code),
            kwargs.pop('category', self.type_code),
            kwargs.pop('name', self.block_code),
            revision=kwargs.pop('revision', self.branch),
            **kwargs,
        )


class DeprecatedLocation(CourseRunUsageKey):  # pylint: disable=abstract-method
    """
    The short-lived location:org+course+run+block_type+block_id syntax.
    """
    CANONICAL_NAMESPACE = 'location'
    URL_RE_SOURCE = """
        (?P<org>{ALLOWED_ID_CHARS}+)\\+(?P<course>{ALLOWED_ID_CHARS}+)\\+(?P<run>{ALLOWED_ID_CHARS}+)\\+
        (?P<block_type>{ALLOWED_ID_CHARS}+)\\+
        (?P<block_id>{ALLOWED_ID_CHARS}+)
        """.format(ALLOWED_ID_CHARS=_Locator.ALLOWED_ID_CHARS)

    URL_RE = re.compile('^' + URL_RE_SOURCE + r'\Z', re.VERBOSE | re.UNICODE)

    def __init__(self, course_key, block_type, block_id):
        if course_key.version_guid is not None:
            raise ValueError("DeprecatedLocations don't support course versions")
        if course_key.branch is not None:
            raise ValueError("DeprecatedLocations don't support course branches")
        super().__init__(course_key, block_type, block_id)

    @classmethod
    def _from_string(cls, serialized):
        """Deserialize from a string."""
        parsed_parts = cls.parse_url(serialized)
        course_key = CourseRunKey(
            org_code=parsed_parts.get('org'),
            course_code=parsed_parts.get('course'),
            run_code=parsed_parts.get('run'),
        )
        block_id = parsed_parts.get('block_id')
        return cls(course_key, parsed_parts.get('block_type'), block_id)

    def _to_string(self):
        """Serialize to a string."""
        parts = [
            self.org, self.course, self.run, self.type_code, self.block_code
        ]
        return "+".join(parts)


class AssetLocation(LocationBase, CourseRunAssetKey):  # pylint: disable=abstract-method
    """Deprecated. Use CourseRunAssetKey."""

    DEPRECATED_TAG = 'c4x'

    def replace(self, **kwargs):
        """Return a new AssetLocation with specified fields replaced."""
        return AssetLocation(
            kwargs.pop('org', self.org),
            kwargs.pop('course', self.course),
            kwargs.pop('run', self.run),
            kwargs.pop('category', self.type_code),
            kwargs.pop('name', self.block_code),
            revision=kwargs.pop('revision', self.branch),
            **kwargs,
        )

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """Deprecated. See CourseRunAssetKey._from_deprecated_string."""
        cls._deprecation_warning()
        return CourseRunAssetKey._from_deprecated_string(serialized)

    @classmethod
    def _from_deprecated_son(cls, id_dict, run):
        """Deprecated. See CourseRunAssetKey._from_deprecated_son."""
        cls._deprecation_warning()
        return CourseRunAssetKey._from_deprecated_son(id_dict, run)
