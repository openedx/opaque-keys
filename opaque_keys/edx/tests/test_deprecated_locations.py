"""
Tests of deprecated Locations and SlashSeparatedCourseKeys
"""
import re

from opaque_keys import InvalidKeyError

from opaque_keys.edx.locator import AssetLocator, BlockUsageLocator, CourseLocator
from opaque_keys.edx.locations import AssetLocation, Location, SlashSeparatedCourseKey
from opaque_keys.edx.tests import TestDeprecated

# Allow protected method access throughout this test file
# pylint: disable=protected-access


class TestLocationDeprecatedBase(TestDeprecated):
    """Base for all Location Test Classes"""
    def check_deprecated_replace(self, cls):
        """
        Both AssetLocation and Location must implement their own replace method. This helps test them.

        NOTE: This replace function accesses deprecated variables and therefore throws multiple deprecation warnings.
        """
        with self.assertDeprecationWarning(count=13):
            loc = cls("foo", "bar", "baz", "cat", "name")
            loc_boo = loc.replace(org='boo')
            loc_copy = loc.replace()
            loc_course_key_replaced = loc.replace(course_key=loc.course_key)
        self.assertTrue(isinstance(loc_boo, BlockUsageLocator))
        self.assertTrue(loc_boo.deprecated)
        self.assertNotEquals(id(loc), id(loc_boo))
        self.assertNotEquals(id(loc), id(loc_copy))
        self.assertNotEquals(loc, loc_boo)
        self.assertEquals(loc, loc_copy)
        self.assertEquals(loc, loc_course_key_replaced)


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

    def test_deprecated_replace(self):
        with self.assertDeprecationWarning(count=3):
            ssck = SlashSeparatedCourseKey("foo", "bar", "baz")
            ssck_boo = ssck.replace(org='boo')
            ssck_copy = ssck.replace()
        self.assertTrue(isinstance(ssck_boo, CourseLocator))
        self.assertTrue(ssck_boo.deprecated)
        self.assertNotEquals(id(ssck), id(ssck_boo))
        self.assertNotEquals(id(ssck), id(ssck_copy))
        self.assertNotEquals(ssck, ssck_boo)
        self.assertEquals(ssck, ssck_copy)


class TestLocation(TestLocationDeprecatedBase):
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

    def test_deprecated_replace(self):
        self.check_deprecated_replace(Location)


class TestAssetLocation(TestLocationDeprecatedBase):
    """Tests that AssetLocation raises a deprecation warning and returns an AssetLocator"""
    def test_deprecated_init(self):
        with self.assertDeprecationWarning():
            loc = AssetLocation("foo", "bar", "baz", "cat", "name")
        self.assertTrue(isinstance(loc, AssetLocator))
        self.assertTrue(loc.deprecated)

    def test_deprecated_replace(self):
        self.check_deprecated_replace(AssetLocation)
