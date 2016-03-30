"""
Tests for opaque_keys.edx.locator.
"""
from unittest import TestCase

import random

from six import text_type
from bson.objectid import ObjectId

from opaque_keys.edx.locator import Locator, CourseLocator, DefinitionLocator, VersionTree
from opaque_keys.edx.keys import DefinitionKey


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
