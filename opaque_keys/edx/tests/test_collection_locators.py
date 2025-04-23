"""
Tests of LibraryCollectionLocator
"""
import ddt
from opaque_keys import InvalidKeyError
from opaque_keys.edx.tests import LocatorBaseTest
from opaque_keys.edx.keys import CollectionKey
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
        lib_key = LibraryLocatorV2(org=org, slug=lib)
        coll_key = LibraryCollectionLocator(lib_key=lib_key, collection_id=code)
        lib_key = coll_key.lib_key
        assert str(coll_key) == "lib-collection:TestX:LibraryX:test-problem-bank"
        assert coll_key.org == org
        assert coll_key.collection_id == code
        assert lib_key.org == org
        assert lib_key.slug == lib
        assert isinstance(coll_key, CollectionKey)

    def test_coll_key_constructor_bad_ids(self):
        lib_key = LibraryLocatorV2(org="TestX", slug="lib1")

        with self.assertRaises(ValueError):
            LibraryCollectionLocator(lib_key=lib_key, collection_id='usage-!@#{$%^&*}')
        with self.assertRaises(TypeError):
            LibraryCollectionLocator(lib_key=None, collection_id='usage')

    def test_coll_key_from_string(self):
        org = 'TestX'
        lib = 'LibraryX'
        code = 'test-problem-bank'
        str_key = f"lib-collection:{org}:{lib}:{code}"
        coll_key = LibraryCollectionLocator.from_string(str_key)
        assert coll_key == CollectionKey.from_string(str_key)
        assert str(coll_key) == str_key
        assert coll_key.org == org
        assert coll_key.collection_id == code
        lib_key = coll_key.lib_key
        assert isinstance(lib_key, LibraryLocatorV2)
        assert lib_key.org == org
        assert lib_key.slug == lib
        assert coll_key.context_key == lib_key

    def test_coll_key_invalid_from_string(self):
        with self.assertRaises(InvalidKeyError):
            LibraryCollectionLocator.from_string("this-is-a-great-test")
        with self.assertRaises(InvalidKeyError):
            LibraryCollectionLocator.from_string("lib-collection:TestX:LibraryX:test:too:many:colons")
