"""
Tests for opaque_keys.edx.locator.
"""
from unittest import TestCase

import random

import ddt
from six import text_type
from bson.objectid import ObjectId

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import DefinitionKey, CourseKey, AggregateCourseKey
from opaque_keys.edx.locator import Locator, CourseLocator, DefinitionLocator, VersionTree, AggregateCourseLocator


class LocatorTests(TestCase):
    """
    Tests for :class:`.Locator`
    """

    def test_cant_instantiate_abstract_class(self):
        self.assertRaises(TypeError, Locator)


class DefinitionLocatorTests(TestCase):
    """
    Tests for :class:`.DefinitionLocator`
    """

    def test_description_locator_url(self):
        object_id = '{:024x}'.format(random.randrange(16 ** 24))
        definition_locator = DefinitionLocator('html', object_id)
        self.assertEqual('def-v1:{}+{}@html'.format(object_id, DefinitionLocator.BLOCK_TYPE_PREFIX),
                         text_type(definition_locator))
        self.assertEqual(definition_locator, DefinitionKey.from_string(text_type(definition_locator)))

    def test_description_locator_version(self):
        object_id = '{:024x}'.format(random.randrange(16 ** 24))
        definition_locator = DefinitionLocator('html', object_id)
        self.assertEqual(object_id, str(definition_locator.version()))


class VersionTreeTests(TestCase):
    """
    Tests for :class:`.VersionTree`
    """

    def test_version_tree(self):
        """
        Test making a VersionTree object.
        """
        with self.assertRaises(TypeError):
            VersionTree("invalid")

        versionless_locator = CourseLocator(org="mit.eecs", course="6.002x", run="2014")
        with self.assertRaises(ValueError):
            VersionTree(versionless_locator)

        test_id_loc = '519665f6223ebd6980884f2b'
        test_id = ObjectId(test_id_loc)
        valid_locator = CourseLocator(version_guid=test_id)
        self.assertEqual(VersionTree(valid_locator).children, [])


@ddt.ddt
class AggregateCourseLocatorTests(TestCase):
    """
    Tests for :class:`.AggregateCourseLocator`
    """

    def test_aggregate_course_locator(self):
        """
        Verify that the method "from_string" of class "AggregateCourseKey"
        returns an object of "AggregateCourseLocator" for a valid course key.
        """
        aggregate_course_key = 'course-v2:org+course'
        aggregate_course_locator = AggregateCourseKey.from_string(aggregate_course_key)
        expected_course_locator = AggregateCourseLocator(org='org', course='course')
        self.assertEqual(expected_course_locator, aggregate_course_locator)

    @ddt.data(
        'org/course/run',
        'course-v1:org+course+run',
    )
    def test_aggregate_course_locator_from_course_key(self, course_id):
        """
        Verify that the method "from_course_key" of class "AggregateCourseLocator"
        coverts a valid course run key to an aggregate course key.
        """
        course_key = CourseKey.from_string(course_id)
        expected_course_key = AggregateCourseLocator(org=course_key.org, course=course_key.course)
        actual_course_key = AggregateCourseLocator.from_course_key(course_key)
        self.assertEqual(expected_course_key, actual_course_key)

    def test_serialize_to_string(self):
        """
        Verify that the method "from_course_key" of class "AggregateCourseLocator"
        coverts a valid course run key to an aggregate course key.
        """
        course_key = CourseKey.from_string('course-v1:org+course+run')
        aggregate_course_locator = AggregateCourseLocator(org=course_key.org, course=course_key.course)
        expected_serialized_key = '{org}+{course}'.format(org=course_key.org, course=course_key.course)
        # pylint: disable=protected-access
        self.assertEqual(expected_serialized_key, aggregate_course_locator._to_string())

    @ddt.data(
        'org/course/run',
        'org+course+run',
        'org+course+run+foo',
        'course-v2:org+course+run',
    )
    def test_invalid_format_course_key(self, course_key):
        """
        Verify that the method "from_string" of class "AggregateCourseKey"
        raises exception "InvalidKeyError" for unsupported key formats.
        """
        with self.assertRaises(InvalidKeyError):
            AggregateCourseKey.from_string(course_key)
