"""
Deprecated OpaqueKey implementations used by XML and Mongo modulestores
"""
from __future__ import absolute_import
import warnings

from opaque_keys.edx.locator import AssetLocator, BlockUsageLocator, CourseLocator

# Python 2.7 by default suppresses DeprecationWarnings. Make sure we show these, always.
warnings.simplefilter('always', DeprecationWarning)

# This file passes through to protected members of the non-deprecated classes,
# and that's ok. It also may not implement all of the current UsageKey methods.
# pylint: disable=protected-access, abstract-method


class SlashSeparatedCourseKey(CourseLocator):
    """Deprecated. Use :class:`locator.CourseLocator`"""
    def __init__(self, org, course, run, **kwargs):
        warnings.warn(
            "SlashSeparatedCourseKey is deprecated! Please use locator.CourseLocator",
            DeprecationWarning
        )
        super(SlashSeparatedCourseKey, self).__init__(org, course, run, deprecated=True, **kwargs)

    @classmethod
    def from_deprecated_string(cls, serialized):
        """Deprecated. Use :class:`locator.CourseLocator.from_string`"""
        warnings.warn(
            "SlashSeparatedCourseKey is deprecated! Please use locator.CourseLocator",
            DeprecationWarning
        )
        return CourseLocator.from_string(serialized)

    @classmethod
    def from_string(cls, serialized):
        """Deprecated. Use :meth:`locator.CourseLocator.from_string`."""
        warnings.warn(
            "SlashSeparatedCourseKey is deprecated! Please use locator.CourseLocator",
            DeprecationWarning
        )
        return CourseLocator.from_string(serialized)


class LocationBase(object):
    """Deprecated. Base class for :class:`Location` and :class:`AssetLocation`"""

    DEPRECATED_TAG = None  # Subclasses should define what DEPRECATED_TAG is

    @classmethod
    def _deprecation_warning(cls):
        """Display a deprecation warning for the given cls"""
        if issubclass(cls, Location):
            warnings.warn(
                "Location is deprecated! Please use locator.BlockUsageLocator",
                DeprecationWarning,
                stacklevel=2
            )
        elif issubclass(cls, AssetLocation):
            warnings.warn(
                "AssetLocation is deprecated! Please use locator.AssetLocator",
                DeprecationWarning,
                stacklevel=2
            )
        else:
            warnings.warn(
                "{} is deprecated!".format(cls),
                DeprecationWarning,
                stacklevel=2
            )

    @property
    def tag(self):
        """Deprecated. Returns the deprecated tag for this Location."""
        self._deprecation_warning()
        warnings.warn("Tag is no longer supported as a property of Locators.", DeprecationWarning)
        return self.DEPRECATED_TAG

    @classmethod
    def _check_location_part(cls, val, regexp):
        """Deprecated. See CourseLocator._check_location_part"""
        cls._deprecation_warning()
        return CourseLocator._check_location_part(val, regexp)

    @classmethod
    def _clean(cls, value, invalid):
        """Deprecated. See BlockUsageLocator._clean"""
        cls._deprecation_warning()
        return BlockUsageLocator._clean(value, invalid)

    @classmethod
    def clean(cls, value):
        """Deprecated. See BlockUsageLocator.clean"""
        cls._deprecation_warning()
        return BlockUsageLocator.clean(value)

    @classmethod
    def clean_keeping_underscores(cls, value):
        """Deprecated. See BlockUsageLocator.clean_keeping_underscores"""
        cls._deprecation_warning()
        return BlockUsageLocator.clean_keeping_underscores(value)

    @classmethod
    def clean_for_url_name(cls, value):
        """Deprecated. See BlockUsageLocator.clean_for_url_name"""
        cls._deprecation_warning()
        return BlockUsageLocator.clean_for_url_name(value)

    @classmethod
    def clean_for_html(cls, value):
        """Deprecated. See BlockUsageLocator.clean_for_html"""
        cls._deprecation_warning()
        return BlockUsageLocator.clean_for_html(value)

    def __init__(self, org, course, run, category, name, revision=None, **kwargs):
        self._deprecation_warning()

        course_key = CourseLocator(
            org=org,
            course=course,
            run=run,
            branch=revision,
            deprecated=True
        )
        super(LocationBase, self).__init__(course_key, category, name, deprecated=True, **kwargs)

    @classmethod
    def from_deprecated_string(cls, serialized):
        """Deprecated. Use :meth:`locator.BlockUsageLocator.from_string`."""
        cls._deprecation_warning()
        return BlockUsageLocator.from_string(serialized)

    @classmethod
    def from_string(cls, serialized):
        """Deprecated. Use :meth:`locator.BlockUsageLocator.from_string`."""
        cls._deprecation_warning()
        return BlockUsageLocator.from_string(serialized)

    @classmethod
    def _from_deprecated_son(cls, id_dict, run):
        """Deprecated. See BlockUsageLocator._from_deprecated_son"""
        cls._deprecation_warning()
        return BlockUsageLocator._from_deprecated_son(id_dict, run)


class Location(LocationBase, BlockUsageLocator):
    """Deprecated. Use :class:`locator.BlockUsageLocator`"""

    DEPRECATED_TAG = 'i4x'


class AssetLocation(LocationBase, AssetLocator):
    """Deprecated. Use :class:`locator.AssetLocator`"""

    DEPRECATED_TAG = 'c4x'

    @classmethod
    def _from_deprecated_string(cls, serialized):
        """Deprecated. See AssetLocator._from_deprecated_string"""
        cls._deprecation_warning()
        return AssetLocator._from_deprecated_string(serialized)
