"""
Tests of LibraryLocators
"""
import ddt

from bson.objectid import ObjectId

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from opaque_keys.edx.locator import LibraryUsageLocator, LibraryLocator, CourseLocator, AssetLocator

from opaque_keys.edx.tests import LocatorBaseTest, TestDeprecated


@ddt.ddt
class TestLibraryLocators(LocatorBaseTest, TestDeprecated):
    """
    Tests of :class:`.LibraryLocator`
    """
    @ddt.data(
        "org/lib/run/foo",
        "org/lib",
        "org+lib+run",
        "org+lib+",
        "org+lib++branch@library",
        "org+ne@t",
        "per%ent+sign",
    )
    def test_lib_key_from_invalid_string(self, lib_id_str):
        with self.assertRaises(InvalidKeyError):
            LibraryLocator.from_string(lib_id_str)

    def test_lib_key_constructor(self):
        org = 'TestX'
        code = 'test-problem-bank'
        lib_key = LibraryLocator(org=org, library=code)
        self.assertEqual(lib_key.org, org)
        self.assertEqual(lib_key.library, code)
        with self.assertDeprecationWarning():
            self.assertEqual(lib_key.course, code)
        with self.assertDeprecationWarning():
            self.assertEqual(lib_key.run, 'library')
        self.assertEqual(lib_key.branch, 'library')

    def test_constructor_using_course(self):
        org = 'TestX'
        code = 'test-problem-bank'
        lib_key = LibraryLocator(org=org, library=code)
        with self.assertDeprecationWarning():
            lib_key2 = LibraryLocator(org=org, course=code)
        self.assertEqual(lib_key, lib_key2)
        self.assertEqual(lib_key2.library, code)

    def test_version_property_deprecated(self):
        lib_key = CourseKey.from_string('library-v1:TestX+lib1+version@519665f6223ebd6980884f2b')
        with self.assertDeprecationWarning():
            self.assertEqual(lib_key.version, ObjectId('519665f6223ebd6980884f2b'))

    def test_invalid_run(self):
        with self.assertRaises(ValueError):
            LibraryLocator(org='TestX', library='test', run='not-library')

    def test_lib_key_inheritance(self):
        lib_key = CourseKey.from_string('library-v1:TestX+lib1')
        self.assertIsInstance(lib_key, CourseKey)  # In future, this may change
        self.assertNotIsInstance(lib_key, CourseLocator)

    def test_lib_key_roundtrip_and_equality(self):
        org = 'TestX'
        code = 'test-problem-bank'
        lib_key = LibraryLocator(org=org, library=code)
        lib_key2 = CourseKey.from_string(unicode(lib_key))
        self.assertEqual(lib_key, lib_key2)

    def test_lib_key_make_usage_key(self):
        lib_key = CourseKey.from_string('library-v1:TestX+lib1')
        usage_key = LibraryUsageLocator(lib_key, 'html', 'html17')
        made = lib_key.make_usage_key('html', 'html17')
        self.assertEquals(usage_key, made)
        self.assertEquals(
            unicode(usage_key),
            unicode(made)
        )

    def test_lib_key_not_deprecated(self):
        lib_key = CourseKey.from_string('library-v1:TestX+lib1')
        self.assertEqual(lib_key.deprecated, False)

    def test_lib_key_no_deprecated_support(self):
        lib_key = CourseKey.from_string('library-v1:TestX+lib1')
        with self.assertRaises(AttributeError):
            lib_key.to_deprecated_string()
        with self.assertRaises(NotImplementedError):
            lib_key._to_deprecated_string()  # pylint: disable=protected-access
        with self.assertRaises(NotImplementedError):
            LibraryLocator._from_deprecated_string('test/test/test')  # pylint: disable=protected-access

    def test_lib_key_no_offering(self):
        with self.assertRaises(ValueError):
            LibraryLocator(org='TestX', library='test', offering='tribble')

    def test_lib_key_branch_support(self):
        org = 'TestX'
        code = 'test-branch-support'
        branch = 'future-purposes-perhaps'
        lib_key = LibraryLocator(org=org, library=code, branch=branch)
        self.assertEqual(lib_key.org, org)
        self.assertEqual(lib_key.library, code)
        self.assertEqual(lib_key.branch, branch)
        lib_key2 = CourseKey.from_string(unicode(lib_key))
        self.assertEqual(lib_key, lib_key2)
        self.assertEqual(lib_key.branch, branch)

        branch2 = "br2"
        branch2_key = lib_key.for_branch(branch2)
        self.assertEqual(branch2_key.branch, branch2)

        normal_branch = lib_key.for_branch(None)
        self.assertNotEqual(normal_branch.branch, None)
        self.assertEqual(normal_branch.branch, LibraryLocator.DEFAULT_BRANCH)

    def test_version_only_lib_key(self):
        version_only_lib_key = LibraryLocator(version_guid=ObjectId('519665f6223ebd6980884f2b'))
        self.assertEqual(version_only_lib_key.org, None)
        self.assertEqual(version_only_lib_key.library, None)
        self.assertEqual(version_only_lib_key.package_id, None)
        with self.assertRaises(InvalidKeyError):
            version_only_lib_key.for_branch("test")

    def test_lib_key_constructor_underspecified(self):
        with self.assertRaises(InvalidKeyError):
            LibraryLocator()
        with self.assertRaises(InvalidKeyError):
            LibraryLocator(branch='published')
        with self.assertRaises(InvalidKeyError):
            LibraryLocator(library='lib5')
        with self.assertRaises(InvalidKeyError):
            LibraryLocator(org='TextX')

    def test_lib_key_constructor_overspecified(self):
        with self.assertRaises(ValueError):
            LibraryLocator(org='TestX', library='big', course='small')

    def test_lib_key_constructor_bad_ids(self):
        with self.assertRaises(InvalidKeyError):
            LibraryLocator(org="!@#{$%^&*}", library="lib1")
        with self.assertRaises(InvalidKeyError):
            LibraryLocator(org="TestX", library="lib+1")
        with self.assertRaises(InvalidKeyError):
            LibraryLocator(org="TestX", library="lib1", branch="!+!")

    def test_lib_key_constructor_bad_version_guid(self):
        with self.assertRaises(ValueError):
            LibraryLocator(version_guid="012345")

        with self.assertRaises(InvalidKeyError):
            LibraryLocator(version_guid=None)

    def test_lib_key_constructor_version_guid(self):
        # generate a random location
        test_id_1 = ObjectId()
        test_id_1_loc = str(test_id_1)
        testobj_1 = LibraryLocator(version_guid=test_id_1)
        self.assertEqual(testobj_1.version_guid, test_id_1)
        self.assertEqual(testobj_1.org, None)
        self.assertEqual(testobj_1.library, None)
        self.assertEqual(str(testobj_1.version_guid), test_id_1_loc)
        # Allow access to _to_string
        # pylint: disable=protected-access
        testobj_1_string = u'@'.join((testobj_1.VERSION_PREFIX, test_id_1_loc))
        self.assertEqual(testobj_1._to_string(), testobj_1_string)
        self.assertEqual(str(testobj_1), u'library-v1:' + testobj_1_string)
        self.assertEqual(testobj_1.html_id(), u'library-v1:' + testobj_1_string)
        self.assertEqual(testobj_1.version_guid, test_id_1)

        # Test using a given string
        test_id_2_loc = '519665f6223ebd6980884f2b'
        test_id_2 = ObjectId(test_id_2_loc)
        testobj_2 = LibraryLocator(version_guid=test_id_2)
        self.assertEqual(testobj_2.version_guid, test_id_2)
        self.assertEqual(testobj_2.org, None)
        self.assertEqual(testobj_2.library, None)
        self.assertEqual(str(testobj_2.version_guid), test_id_2_loc)
        # Allow access to _to_string
        # pylint: disable=protected-access
        testobj_2_string = u'@'.join((testobj_2.VERSION_PREFIX, test_id_2_loc))
        self.assertEqual(testobj_2._to_string(), testobj_2_string)
        self.assertEqual(str(testobj_2), u'library-v1:' + testobj_2_string)
        self.assertEqual(testobj_2.html_id(), u'library-v1:' + testobj_2_string)
        self.assertEqual(testobj_2.version_guid, test_id_2)

    def test_library_constructor_version_url(self):
        # Test parsing a url when it starts with a version ID and there is also a block ID.
        # This hits the parsers parse_guid method.
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = CourseKey.from_string("library-v1:{}@{}+{}@hw3".format(
            LibraryLocator.VERSION_PREFIX, test_id_loc, LibraryLocator.BLOCK_PREFIX
        ))
        self.assertEqual(testobj.version_guid, ObjectId(test_id_loc))
        self.assertEqual(testobj.org, None)
        self.assertEqual(testobj.library, None)

    def test_changing_course(self):
        lib_key = LibraryLocator(org="TestX", library="test")
        with self.assertRaises(AttributeError):
            lib_key.course = "PHYS"
        with self.assertRaises(KeyError):
            lib_key.replace(course="PHYS")

    def test_make_asset_key(self):
        lib_key = CourseKey.from_string('library-v1:TestX+lib1')
        self.assertEquals(
            AssetLocator(lib_key, 'asset', 'foo.bar'),
            lib_key.make_asset_key('asset', 'foo.bar')
        )

    def test_versions(self):
        lib_key = CourseKey.from_string('library-v1:TestX+lib1+version@519665f6223ebd6980884f2b')
        lib_key2 = CourseKey.from_string('library-v1:TestX+lib1')
        lib_key3 = lib_key.version_agnostic()
        self.assertEqual(lib_key2, lib_key3)
        self.assertEqual(lib_key3.version_guid, None)

        new_version = '123445678912345678912345'
        lib_key4 = lib_key.for_version(new_version)
        self.assertEqual(lib_key4.version_guid, ObjectId(new_version))

    def test_course_agnostic(self):
        lib_key = CourseKey.from_string('library-v1:TestX+lib1+version@519665f6223ebd6980884f2b')
        lib_key2 = CourseKey.from_string('library-v1:version@519665f6223ebd6980884f2b')
        lib_key3 = lib_key.course_agnostic()
        self.assertEqual(lib_key2, lib_key3)
        self.assertEqual(lib_key3.org, None)
        self.assertEqual(lib_key3.library, None)
