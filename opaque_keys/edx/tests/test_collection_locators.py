"""
Tests of LibraryCollectionLocator
"""
import ddt
from opaque_keys import InvalidKeyError
from opaque_keys.edx.tests import LocatorBaseTest
from opaque_keys.edx.locator import LibraryCollectionLocator, LibraryLocatorV2


@ddt.ddt
class TestLibraryCollectionLocator(LocatorBaseTest):
    """
    Tests of :class:`.LibraryCollectionLocator`
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
            LibraryCollectionLocator.from_string(coll_id_str)

    def test_coll_key_constructor(self):
        org = 'TestX'
        lib = 'LibraryX'
        code = 'test-problem-bank'
        library_key = LibraryLocatorV2(org=org, slug=lib)
        coll_key = LibraryCollectionLocator(library_key=library_key, collection_id=code)
        library_key = coll_key.library_key
        self.assertEqual(str(coll_key), "lib-collection:TestX:LibraryX:test-problem-bank")
        self.assertEqual(coll_key.org, org)
        self.assertEqual(coll_key.collection_id, code)
        self.assertEqual(library_key.org, org)
        self.assertEqual(library_key.slug, lib)

    def test_coll_key_constructor_bad_ids(self):
        library_key = LibraryLocatorV2(org="TestX", slug="lib1")

        with self.assertRaises(ValueError):
            LibraryCollectionLocator(library_key=library_key, collection_id='usage-!@#{$%^&*}')
        with self.assertRaises(TypeError):
            LibraryCollectionLocator(library_key=None, collection_id='usage')

    def test_coll_key_from_string(self):
        org = 'TestX'
        lib = 'LibraryX'
        code = 'test-problem-bank'
        str_key = f"lib-collection:{org}:{lib}:{code}"
        coll_key = LibraryCollectionLocator.from_string(str_key)
        library_key = coll_key.library_key
        self.assertEqual(str(coll_key), str_key)
        self.assertEqual(coll_key.org, org)
        self.assertEqual(coll_key.collection_id, code)
        self.assertEqual(library_key.org, org)
        self.assertEqual(library_key.slug, lib)

    def test_coll_key_invalid_from_string(self):
        with self.assertRaises(InvalidKeyError):
            LibraryCollectionLocator.from_string("this-is-a-great-test")
