"""
Tests of LibraryContainerLocator
"""
import ddt
from opaque_keys import InvalidKeyError
from opaque_keys.edx.tests import LocatorBaseTest
from opaque_keys.edx.locator import LibraryContainerLocator, LibraryLocatorV2


@ddt.ddt
class TestLibraryContainerLocator(LocatorBaseTest):
    """
    Tests of :class:`.LibraryContainerLocator`
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
            LibraryContainerLocator.from_string(coll_id_str)

    def test_key_constructor(self):
        org = 'TestX'
        lib = 'LibraryX'
        container_type = 'unit'
        container_id = 'test-container'
        library_key = LibraryLocatorV2(org=org, slug=lib)
        container_key = LibraryContainerLocator(
            library_key=library_key,
            container_type=container_type,
            container_id=container_id,
        )
        library_key = container_key.library_key
        self.assertEqual(str(container_key), "lct:TestX:LibraryX:unit:test-container")
        self.assertEqual(container_key.org, org)
        self.assertEqual(container_key.container_type, container_type)
        self.assertEqual(container_key.container_id, container_id)
        self.assertEqual(library_key.org, org)
        self.assertEqual(library_key.slug, lib)

    def test_key_constructor_bad_ids(self):
        library_key = LibraryLocatorV2(org="TestX", slug="lib1")

        with self.assertRaises(TypeError):
            LibraryContainerLocator(library_key=None, container_type='unit', container_id='usage')

        with self.assertRaises(ValueError):
            LibraryContainerLocator(library_key=library_key, container_type='unit', container_id='usage-!@#{$%^&*}')

    def test_key_constructor_bad_type(self):
        library_key = LibraryLocatorV2(org="TestX", slug="lib1")

        with self.assertRaises(ValueError):
            LibraryContainerLocator(library_key=library_key, container_type='unit-!@#{$%^&*}', container_id='usage')

    def test_key_from_string(self):
        org = 'TestX'
        lib = 'LibraryX'
        container_type = 'unit'
        container_id = 'test-container'
        str_key = f"lct:{org}:{lib}:{container_type}:{container_id}"
        container_key = LibraryContainerLocator.from_string(str_key)
        library_key = container_key.library_key
        self.assertEqual(str(container_key), str_key)
        self.assertEqual(container_key.org, org)
        self.assertEqual(container_key.container_type, container_type)
        self.assertEqual(container_key.container_id, container_id)
        self.assertEqual(library_key.org, org)
        self.assertEqual(library_key.slug, lib)
