"""
Tests of LibCollectionLocator
"""
import ddt
from opaque_keys import InvalidKeyError
from opaque_keys.edx.tests import LocatorBaseTest
from opaque_keys.edx.locator import LibCollectionLocator, LibraryLocatorV2


@ddt.ddt
class TestLibCollectionLocator(LocatorBaseTest):
    """
    Tests of :class:`.LibCollectionLocator`
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
            LibCollectionLocator.from_string(coll_id_str)

    def test_coll_key_constructor(self):
        org = 'TestX'
        lib = 'LibraryX'
        code = 'test-problem-bank'
        lib_key = LibraryLocatorV2(org=org, slug=lib)
        coll_key = LibCollectionLocator(lib_key=lib_key, usage_id=code)
        lib_key = coll_key.context_key
        self.assertEqual(str(coll_key), "lib-collection:TestX:LibraryX:test-problem-bank")
        self.assertEqual(coll_key.org, org)
        self.assertEqual(coll_key.lib, lib)
        self.assertEqual(coll_key.usage_id, code)
        self.assertEqual(lib_key.org, org)
        self.assertEqual(lib_key.slug, lib)

    def test_coll_key_constructor_bad_ids(self):
        lib_key = LibraryLocatorV2(org="TestX", slug="lib1")

        with self.assertRaises(ValueError):
            LibCollectionLocator(lib_key=lib_key, usage_id='usage-!@#{$%^&*}')
        with self.assertRaises(TypeError):
            LibCollectionLocator(lib_key=None, usage_id='usage')

    def test_coll_key_from_string(self):
        org = 'TestX'
        lib = 'LibraryX'
        code = 'test-problem-bank'
        str_key = f"lib-collection:{org}:{lib}:{code}"
        coll_key = LibCollectionLocator.from_string(str_key)
        lib_key = coll_key.context_key
        self.assertEqual(str(coll_key), str_key)
        self.assertEqual(coll_key.org, org)
        self.assertEqual(coll_key.lib, lib)
        self.assertEqual(coll_key.usage_id, code)
        self.assertEqual(lib_key.org, org)
        self.assertEqual(lib_key.slug, lib)

    def test_coll_key_invalid_from_string(self):
        with self.assertRaises(InvalidKeyError):
            LibCollectionLocator.from_string("this-is-a-great-test")
