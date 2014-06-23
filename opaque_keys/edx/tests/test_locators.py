"""
Tests for opaque_keys.edx.locator.
"""
from unittest import TestCase

import random
from bson.objectid import ObjectId
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import Locator, CourseLocator, BlockUsageLocator, DefinitionLocator, VersionTree
from ddt import ddt, data
from opaque_keys.edx.keys import UsageKey, CourseKey, DefinitionKey


@ddt
class LocatorTest(TestCase):
    """
    Tests for subclasses of Locator.
    """

    def test_cant_instantiate_abstract_class(self):
        self.assertRaises(TypeError, Locator)

    def test_course_constructor_underspecified(self):
        with self.assertRaises(InvalidKeyError):
            CourseLocator()
        with self.assertRaises(InvalidKeyError):
            CourseLocator(branch='published')

    def test_course_constructor_bad_version_guid(self):
        with self.assertRaises(ValueError):
            CourseLocator(version_guid="012345")

        with self.assertRaises(InvalidKeyError):
            CourseLocator(version_guid=None)

    def test_course_constructor_version_guid(self):
        # generate a random location
        test_id_1 = ObjectId()
        test_id_1_loc = str(test_id_1)
        testobj_1 = CourseLocator(version_guid=test_id_1)
        self.check_course_locn_fields(testobj_1, version_guid=test_id_1)
        self.assertEqual(str(testobj_1.version_guid), test_id_1_loc)
        # Allow access to _to_string
        # pylint: disable=protected-access
        testobj_1_string = u'+'.join((testobj_1.VERSION_PREFIX, test_id_1_loc))
        self.assertEqual(testobj_1._to_string(), testobj_1_string)
        self.assertEqual(str(testobj_1), u'course-locator:' + testobj_1_string)
        self.assertEqual(testobj_1.html_id(), u'course-locator:' + testobj_1_string)
        self.assertEqual(testobj_1.version(), test_id_1)

        # Test using a given string
        test_id_2_loc = '519665f6223ebd6980884f2b'
        test_id_2 = ObjectId(test_id_2_loc)
        testobj_2 = CourseLocator(version_guid=test_id_2)
        self.check_course_locn_fields(testobj_2, version_guid=test_id_2)
        self.assertEqual(str(testobj_2.version_guid), test_id_2_loc)
        # Allow access to _to_string
        # pylint: disable=protected-access
        testobj_2_string = u'+'.join((testobj_2.VERSION_PREFIX, test_id_2_loc))
        self.assertEqual(testobj_2._to_string(), testobj_2_string)
        self.assertEqual(str(testobj_2), u'course-locator:' + testobj_2_string)
        self.assertEqual(testobj_2.html_id(), u'course-locator:' + testobj_2_string)
        self.assertEqual(testobj_2.version(), test_id_2)

    @data(
        ' mit.eecs',
        'mit.eecs ',
        CourseLocator.VERSION_PREFIX + '+mit.eecs',
        BlockUsageLocator.BLOCK_PREFIX + '+black+mit.eecs',
        'mit.ee cs',
        'mit.ee,cs',
        'mit.ee+cs',
        'mit.ee&cs',
        'mit.ee()cs',
        CourseLocator.BRANCH_PREFIX + '+this',
        'mit.eecs+' + CourseLocator.BRANCH_PREFIX,
        'mit.eecs+' + CourseLocator.BRANCH_PREFIX + '+this+' + CourseLocator.BRANCH_PREFIX + '+that',
        'mit.eecs+' + CourseLocator.BRANCH_PREFIX + '+this+' + CourseLocator.BRANCH_PREFIX,
        'mit.eecs+' + CourseLocator.BRANCH_PREFIX + '+this ',
        'mit.eecs+' + CourseLocator.BRANCH_PREFIX + '+th%is ',
    )
    def test_course_constructor_bad_package_id(self, bad_id):
        """
        Test all sorts of badly-formed package_ids (and urls with those package_ids)
        """
        with self.assertRaises(InvalidKeyError):
            CourseLocator(org=bad_id, course='test', run='2014_T2')

        with self.assertRaises(InvalidKeyError):
            CourseLocator(org='test', course=bad_id, run='2014_T2')

        with self.assertRaises(InvalidKeyError):
            CourseKey.from_string('course-locator:test+{}+2014_T2'.format(bad_id))

    @data('course-locator:', 'course-locator:/mit.eecs', 'http:mit.eecs')
    def test_course_constructor_bad_url(self, bad_url):
        with self.assertRaises(InvalidKeyError):
            CourseKey.from_string(bad_url)

    def test_course_constructor_url(self):
        # Test parsing a url when it starts with a version ID and there is also a block ID.
        # This hits the parsers parse_guid method.
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = CourseKey.from_string("course-locator:{}+{}+{}+hw3".format(
            CourseLocator.VERSION_PREFIX, test_id_loc, CourseLocator.BLOCK_PREFIX
        ))
        self.check_course_locn_fields(
            testobj,
            version_guid=ObjectId(test_id_loc)
        )

    def test_course_constructor_url_package_id_and_version_guid(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = CourseKey.from_string(
            'course-locator:mit.eecs+honors.6002x+2014_T2+{}+{}'.format(CourseLocator.VERSION_PREFIX, test_id_loc)
        )
        self.check_course_locn_fields(
            testobj,
            org='mit.eecs',
            course='honors.6002x',
            run='2014_T2',
            version_guid=ObjectId(test_id_loc)
        )

    def test_course_constructor_url_package_id_branch_and_version_guid(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        org = 'mit.eecs'
        course = '~6002x'
        run = '2014_T2'
        testobj = CourseKey.from_string('course-locator:{}+{}+{}+{}+draft-1+{}+{}'.format(
            org, course, run, CourseLocator.BRANCH_PREFIX, CourseLocator.VERSION_PREFIX, test_id_loc
        ))
        self.check_course_locn_fields(
            testobj,
            org=org,
            course=course,
            run=run,
            branch='draft-1',
            version_guid=ObjectId(test_id_loc)
        )

    def test_course_constructor_package_id_no_branch(self):
        org = 'mit.eecs'
        course = '6002x'
        run = '2014_T2'
        testurn = '{}+{}+{}'.format(org, course, run)
        testobj = CourseLocator(org=org, course=course, run=run)
        self.check_course_locn_fields(testobj, org=org, course=course, run=run)
        # Allow access to _to_string
        # pylint: disable=protected-access
        self.assertEqual(testobj._to_string(), testurn)

    def test_course_constructor_package_id_separate_branch(self):
        org = 'mit.eecs'
        course = '6002x'
        run = '2014_T2'
        test_branch = 'published'
        expected_urn = '{}+{}+{}+{}+{}'.format(org, course, run, CourseLocator.BRANCH_PREFIX, test_branch)
        testobj = CourseLocator(org=org, course=course, run=run, branch=test_branch)
        self.check_course_locn_fields(
            testobj,
            org=org,
            course=course,
            run=run,
            branch=test_branch,
        )
        self.assertEqual(testobj.branch, test_branch)
        # Allow access to _to_string
        # pylint: disable=protected-access
        self.assertEqual(testobj._to_string(), expected_urn)

    def test_block_constructor(self):
        expected_org = 'mit.eecs'
        expected_course = '6002x'
        expected_run = '2014_T2'
        expected_branch = 'published'
        expected_block_ref = 'HW3'
        testurn = 'edx:{}+{}+{}+{}+{}+{}+{}+{}+{}'.format(
            expected_org, expected_course, expected_run, CourseLocator.BRANCH_PREFIX, expected_branch,
            BlockUsageLocator.BLOCK_TYPE_PREFIX, 'problem', BlockUsageLocator.BLOCK_PREFIX, 'HW3'
        )
        testobj = UsageKey.from_string(testurn)
        self.check_block_locn_fields(
            testobj,
            org=expected_org,
            course=expected_course,
            run=expected_run,
            branch=expected_branch,
            block_type='problem',
            block=expected_block_ref
        )
        self.assertEqual(unicode(testobj), testurn)
        testobj = testobj.for_version(ObjectId())
        agnostic = testobj.version_agnostic()
        self.assertIsNone(agnostic.version_guid)
        self.check_block_locn_fields(
            agnostic,
            org=expected_org,
            course=expected_course,
            run=expected_run,
            branch=expected_branch,
            block=expected_block_ref
        )

    def test_block_constructor_url_version_prefix(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = UsageKey.from_string(
            'edx:mit.eecs+6002x+2014_T2+{}+{}+{}+problem+{}+lab2'.format(
                CourseLocator.VERSION_PREFIX,
                test_id_loc,
                BlockUsageLocator.BLOCK_TYPE_PREFIX,
                BlockUsageLocator.BLOCK_PREFIX
            )
        )
        self.check_block_locn_fields(
            testobj,
            org='mit.eecs',
            course='6002x',
            run='2014_T2',
            block_type='problem',
            block='lab2',
            version_guid=ObjectId(test_id_loc)
        )
        agnostic = testobj.course_agnostic()
        self.check_block_locn_fields(
            agnostic,
            block='lab2',
            org=None,
            course=None,
            run=None,
            version_guid=ObjectId(test_id_loc)
        )
        self.assertIsNone(agnostic.course)
        self.assertIsNone(agnostic.run)
        self.assertIsNone(agnostic.org)

    def test_block_constructor_url_kitchen_sink(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = UsageKey.from_string(
            'edx:mit.eecs+6002x+2014_T2+{}+draft+{}+{}+{}+problem+{}+lab2'.format(
                CourseLocator.BRANCH_PREFIX, CourseLocator.VERSION_PREFIX, test_id_loc,
                BlockUsageLocator.BLOCK_TYPE_PREFIX, BlockUsageLocator.BLOCK_PREFIX
            )
        )
        self.check_block_locn_fields(
            testobj,
            org='mit.eecs',
            course='6002x',
            run='2014_T2',
            branch='draft',
            block='lab2',
            version_guid=ObjectId(test_id_loc)
        )

    def test_make_usage_key(self):
        # Deprecated CourseKeys should return deprecated strings
        course_key = CourseKey.from_string("foo/bar/baz")
        usage_key = unicode(course_key.make_usage_key('html', 'test_html'))
        self.assertEqual(usage_key, "i4x://foo/bar/html/test_html")

        # Newer CourseKeys should return regular strings
        course_key = CourseLocator("foo", "bar", "baz")
        usage_key = unicode(course_key.make_usage_key('html', 'test_html'))
        self.assertEqual(usage_key, "edx:foo+bar+baz+type+html+block+test_html")

    def test_make_asset_key(self):
        # Deprecated AssetKeys should return deprecated strings
        course_key = CourseKey.from_string("foo/bar/baz")
        asset_key = unicode(course_key.make_asset_key("picture", "path.jpg"))
        self.assertEqual(asset_key, "/c4x/foo/bar/picture/path.jpg")

        # Newer AssetKeys should return regular strings
        course_key = CourseLocator("foo", "bar", "baz")
        asset_key = unicode(course_key.make_asset_key("picture", "path.jpg"))
        self.assertEqual(asset_key, "asset-location:foo+bar+baz+picture+path.jpg")

    def test_colon_name(self):
        """
        It seems we used to use colons in names; so, ensure they're acceptable.
        """
        org = 'mit.eecs'
        course = 'foo'
        run = '2014_T2'
        branch = 'foo'
        block_id = 'problem:with-colon~2'
        testobj = BlockUsageLocator(
            CourseLocator(org=org, course=course, run=run, branch=branch),
            block_type='problem',
            block_id=block_id
        )
        self.check_block_locn_fields(
            testobj, org=org, course=course, run=run, branch=branch, block=block_id
        )

    def test_relative(self):
        """
        Test making a relative usage locator.
        """
        org = 'mit.eecs'
        course = 'ponypower'
        run = "2014_T2"
        branch = 'foo'
        baseobj = CourseLocator(org=org, course=course, run=run, branch=branch)
        block_id = 'problem:with-colon~2'
        testobj = BlockUsageLocator.make_relative(baseobj, 'problem', block_id)
        self.check_block_locn_fields(
            testobj, org=org, course=course, run=run, branch=branch, block=block_id
        )
        block_id = 'completely_different'
        testobj = BlockUsageLocator.make_relative(testobj, 'problem', block_id)
        self.check_block_locn_fields(
            testobj, org=org, course=course, run=run, branch=branch, block=block_id
        )

    def test_repr(self):
        testurn = u'edx:mit.eecs+6002x+2014_T2+{}+published+{}+problem+{}+HW3'.format(
            CourseLocator.BRANCH_PREFIX, BlockUsageLocator.BLOCK_TYPE_PREFIX, BlockUsageLocator.BLOCK_PREFIX
        )
        testobj = UsageKey.from_string(testurn)
        self.assertEqual("BlockUsageLocator(CourseLocator(u'mit.eecs', u'6002x', u'2014_T2', u'published', None), u'problem', u'HW3')", repr(testobj))

    def test_description_locator_url(self):
        object_id = '{:024x}'.format(random.randrange(16 ** 24))
        definition_locator = DefinitionLocator('html', object_id)
        self.assertEqual('defx:{}+{}+html'.format(object_id, DefinitionLocator.BLOCK_TYPE_PREFIX), unicode(definition_locator))
        self.assertEqual(definition_locator, DefinitionKey.from_string(unicode(definition_locator)))

    def test_description_locator_version(self):
        object_id = '{:024x}'.format(random.randrange(16 ** 24))
        definition_locator = DefinitionLocator('html', object_id)
        self.assertEqual(object_id, str(definition_locator.version()))

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

    # ------------------------------------------------------------------
    # Utilities

    def check_course_locn_fields(self, testobj, version_guid=None,
                                 org=None, course=None, run=None, branch=None):
        """
        Checks the version, org, course, run, and branch in testobj
        """
        self.assertEqual(testobj.version_guid, version_guid)
        self.assertEqual(testobj.org, org)
        self.assertEqual(testobj.course, course)
        self.assertEqual(testobj.run, run)
        self.assertEqual(testobj.branch, branch)

    def check_block_locn_fields(self, testobj, version_guid=None,
                                org=None, course=None, run=None, branch=None, block_type=None, block=None):
        """
        Does adds a block id check over and above the check_course_locn_fields tests
        """
        self.check_course_locn_fields(testobj, version_guid, org, course, run,
                                      branch)
        if block_type is not None:
            self.assertEqual(testobj.block_type, block_type)
        self.assertEqual(testobj.block_id, block)
