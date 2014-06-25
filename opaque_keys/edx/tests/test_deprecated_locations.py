"""
Tests of deprecated Locations and SlashSeparatedCourseKeys
"""
import re
import warnings
from unittest import TestCase
from contextlib import contextmanager

from opaque_keys import InvalidKeyError

from opaque_keys.edx.locator import AssetLocator, BlockUsageLocator, CourseLocator
from opaque_keys.edx.locations import AssetLocation, Location, SlashSeparatedCourseKey

# Allow protected method access throughout this test file
# pylint: disable=protected-access


class TestDeprecated(TestCase):
    """Base class (with utility methods) for deprecated Location tests"""
    @contextmanager
    def assertDeprecationWarning(self, count=1):
        """Asserts that the contained code raises `count` deprecation warnings"""
        with warnings.catch_warnings(record=True) as caught:
            yield
        self.assertEquals(count, len([warning for warning in caught if issubclass(warning.category, DeprecationWarning)]))


class TestSSCK(TestDeprecated):
    """Tests that SSCK raises a deprecation warning and returns a CourseLocator"""
    def test_deprecated_init(self):
        with self.assertDeprecationWarning():
            ssck = SlashSeparatedCourseKey("foo", "bar", "baz")
        self.assertTrue(isinstance(ssck, CourseLocator))
        self.assertTrue(ssck.deprecated)

    def test_deprecated_from_string(self):
        with self.assertDeprecationWarning():
            with self.assertRaises(InvalidKeyError):
                SlashSeparatedCourseKey.from_string("slashes:foo+bar+baz")

    def test_deprecated_from_string_bad(self):
        with self.assertDeprecationWarning():
            with self.assertRaises(InvalidKeyError):
                SlashSeparatedCourseKey.from_string("foo+bar")

    def test_deprecated_from_dep_string(self):
        with self.assertDeprecationWarning():
            ssck = SlashSeparatedCourseKey.from_deprecated_string("foo/bar/baz")
        self.assertTrue(isinstance(ssck, CourseLocator))

    def test_deprecated_from_dep_string_bad(self):
        with self.assertDeprecationWarning():
            with self.assertRaises(InvalidKeyError):
                SlashSeparatedCourseKey.from_string("foo/bar")


class TestLocation(TestDeprecated):
    """Tests that Location raises a deprecation warning and returns a BlockUsageLocator"""
    def test_deprecated_init(self):
        with self.assertDeprecationWarning():
            loc = Location("foo", "bar", "baz", "cat", "name")
        self.assertTrue(isinstance(loc, BlockUsageLocator))
        self.assertTrue(loc.deprecated)

    def test_clean(self):

        with self.assertDeprecationWarning(count=6):
            with self.assertRaises(InvalidKeyError):
                Location._check_location_part('abc123', re.compile(r'\d'))

            self.assertEquals('abc_', Location._clean('abc123', re.compile(r'\d')))
            self.assertEquals('a._%-', Location.clean('a.*:%-'))
            self.assertEquals('a.__%-', Location.clean_keeping_underscores('a.*:%-'))
            self.assertEquals('a._:%-', Location.clean_for_url_name('a.*:%-'))
            self.assertEquals('a_-', Location.clean_for_html('a.*:%-'))


class TestAssetLocation(TestDeprecated):
    """Tests that AssetLocation raises a deprecation warning and returns an AssetLocator"""
    def test_deprecated_init(self):
        with self.assertDeprecationWarning():
            loc = AssetLocation("foo", "bar", "baz", "cat", "name")
        self.assertTrue(isinstance(loc, AssetLocator))
        self.assertTrue(loc.deprecated)
