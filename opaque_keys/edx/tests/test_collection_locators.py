"""
Tests of CollectionLocator
"""
import ddt
from opaque_keys import InvalidKeyError
from opaque_keys.edx.tests import LocatorBaseTest
from opaque_keys.edx.locator import CollectionLocator


@ddt.ddt
class TestCollectionLocator(LocatorBaseTest):
    """
    Tests of :class:`.CollectionLocator`
    """
    @ddt.data(
        "org/lib/id/foo",
        "org/lib/id",
        "org+lib+id",
        "org+lib+",
        "org+lib++id@library",
        "org+ne@t",
        "per%ent+sign",
    )
    def test_coll_key_from_invalid_string(self, coll_id_str):
        with self.assertRaises(InvalidKeyError):
            CollectionLocator.from_string(coll_id_str)

    def test_coll_key_constructor(self):
        org = 'TestX'
        lib = 'LibraryX'
        code = 'test-problem-bank'
        coll_key = CollectionLocator(org=org, lib=lib, usage_id=code)
        lib_key = coll_key.context_key
        self.assertEqual(coll_key.org, org)
        self.assertEqual(coll_key.lib, lib)
        self.assertEqual(coll_key.usage_id, code)
        self.assertEqual(lib_key.org, org)
        self.assertEqual(lib_key.slug, lib)

    def test_coll_key_constructor_bad_ids(self):
        with self.assertRaises(ValueError):
            CollectionLocator(org="!@#{$%^&*}", lib="lib1", usage_id='usage-id')
        with self.assertRaises(ValueError):
            CollectionLocator(org="TestX", lib="lib+1", usage_id='usage-id')
        with self.assertRaises(ValueError):
            CollectionLocator(org="TestX", lib="lib1", usage_id='usage-!@#{$%^&*}')
