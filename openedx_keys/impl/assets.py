"""
openedx_keys.impl.assets — asset key hierarchy.

Renames from opaque_keys.edx:
  AssetKey     -> AssetKey       (unchanged name)
  AssetLocator -> CourseRunAssetKey
"""
from __future__ import annotations

import re
import warnings
from abc import abstractmethod

from opaque_keys import InvalidKeyError, OpaqueKey
from openedx_keys.impl.base import CourseObjectMixin
from openedx_keys.impl.contexts import CourseRunKey, _Locator
from openedx_keys.impl.usages import CourseRunUsageKey

__all__ = [
    'AssetKey',
    'CourseRunAssetKey',
]


class AssetKey(CourseObjectMixin, OpaqueKey):  # pylint: disable=abstract-method
    """
    An OpaqueKey identifying a course asset. Unchanged name.
    """
    KEY_TYPE = 'asset_key'
    __slots__ = ()

    @property
    @abstractmethod
    def type_code(self) -> str:  # pragma: no cover
        """Return the asset type code."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def path(self) -> str:  # pragma: no cover
        """Return the path for this asset."""
        raise NotImplementedError()


class CourseRunAssetKey(CourseRunUsageKey, AssetKey):  # pylint: disable=abstract-method
    """
    An AssetKey implementation for assets in a course run.

    Renamed from AssetLocator. Inherits type_code and block_code from
    CourseRunUsageKey. path is an alias for block_code (without deprecation).
    """
    CANONICAL_NAMESPACE = 'asset-v1'
    DEPRECATED_TAG = 'c4x'
    __slots__ = CourseRunUsageKey.KEY_FIELDS

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

    ALLOWED_ID_RE = CourseRunUsageKey.DEPRECATED_ALLOWED_ID_RE
    # Allow empty asset ids (used to generate a prefix url)
    DEPRECATED_ALLOWED_ID_RE = re.compile(
        r'^' + _Locator.DEPRECATED_ALLOWED_ID_CHARS + r'+\Z', re.UNICODE
    )

    @property
    def path(self):
        """Return the block_code (file path) for this asset."""
        return self.block_code

    @property
    def asset_type(self):
        """Deprecated. Use type_code."""
        warnings.warn(
            "asset_type is deprecated; use type_code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.type_code

    @property
    def tag(self):
        """Return the deprecated tag for this asset."""
        return self.DEPRECATED_TAG

    def replace(self, **kwargs):
        """Replace KEY_FIELDS; also maps legacy 'path' and 'asset_type' names."""
        if 'path' in kwargs and 'block_code' not in kwargs:
            kwargs['block_code'] = kwargs.pop('path')
        if 'asset_type' in kwargs and 'type_code' not in kwargs:
            kwargs['type_code'] = kwargs.pop('asset_type')
        return super().replace(**kwargs)

    def _to_deprecated_string(self):
        """Return old-style /c4x/ URL."""
        url = (
            f"/{self.DEPRECATED_TAG}/{self.course_key.org_code}"
            f"/{self.course_key.course_code}"
            f"/{self.type_code}/{self.block_code}"
        )
        if self.course_key.branch:
            url += f'@{self.course_key.branch}'
        return url

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """Deserialize from deprecated /c4x/ URL."""
        match = cls.ASSET_URL_RE.match(serialized)
        if match is None:
            raise InvalidKeyError(cls, serialized)
        groups = match.groupdict()
        course_key = CourseRunKey(
            org_code=groups['org'],
            course_code=groups['course'],
            run_code=None,
            branch=groups.get('revision', None),
            deprecated=True,
        )
        return cls(course_key, groups['category'], groups['name'], deprecated=True)

    def to_deprecated_list_repr(self):
        """
        Return the pre-opaque Location fields as an array in old order.
        """
        return ['c4x', self.org, self.course, self.type_code, self.block_code, None]


# Register CourseRunAssetKey as the deprecated fallback for AssetKey
AssetKey.set_deprecated_fallback(CourseRunAssetKey)
