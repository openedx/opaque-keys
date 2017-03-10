"""
Tests of CourseKeys and CourseLocators
"""
from six import text_type

import ddt
import itertools  # pylint: disable=wrong-import-order

from bson.objectid import ObjectId

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator, CourseLocatorV2

from opaque_keys.edx.tests import LocatorBaseTest, TestDeprecated


@ddt.ddt
class TestCourseKeys(LocatorBaseTest, TestDeprecated):
    """
    Tests of :class:`.CourseKey` and :class:`.CourseLocator`
    """
    @ddt.data(
        "foo/bar/baz",
    )
    def test_deprecated_roundtrip(self, course_id):
        self.assertEqual(
            course_id,
            text_type(CourseKey.from_string(course_id))
        )

    @ddt.data(
        "foo!/bar/baz",
    )
    def test_invalid_chars_in_ssck_string(self, course_id):
        with self.assertRaises(InvalidKeyError):
            CourseKey.from_string(course_id)

    @ddt.data(
        "org/course/run/foo",
        "org/course",
        "org+course+run+foo",
        "org+course",
    )
    def test_invalid_format_location(self, course_id):
        with self.assertRaises(InvalidKeyError):
            CourseLocator.from_string(course_id)

    def test_make_usage_key(self):
        depr_course = CourseKey.from_string('org/course/run')
        self.assertEqual(
            text_type(BlockUsageLocator(depr_course, 'category', 'name', deprecated=True)),
            text_type(depr_course.make_usage_key('category', 'name'))
        )

        course = CourseKey.from_string('course-v1:org+course+run')
        self.assertEqual(
            text_type(BlockUsageLocator(course, 'block_type', 'block_id')),
            text_type(course.make_usage_key('block_type', 'block_id'))
        )

    def test_convert_deprecation(self):
        depr_course = CourseKey.from_string('org/course/run')
        course = CourseKey.from_string('course-v1:org+course+run')

        self.assertEqual(text_type(depr_course.replace(deprecated=False)), text_type(course))
        self.assertEqual(text_type(course.replace(deprecated=True)), text_type(depr_course))

    def test_course_constructor_underspecified(self):
        with self.assertRaises(InvalidKeyError):
            CourseLocator()
        with self.assertRaises(InvalidKeyError):
            CourseLocator(branch='published')

    def test_course_constructor_bad_version_guid(self):
        with self.assertRaises(InvalidKeyError):
            CourseLocator(version_guid="012345")

        with self.assertRaises(InvalidKeyError):
            CourseLocator(version_guid=None)

    def test_course_constructor_version_guid(self):
        # pylint: disable=no-member,protected-access

        # generate a random location
        test_id_1 = ObjectId()
        test_id_1_loc = str(test_id_1)
        testobj_1 = CourseLocator(version_guid=test_id_1)
        self.check_course_locn_fields(testobj_1, version_guid=test_id_1)
        self.assertEqual(str(testobj_1.version_guid), test_id_1_loc)

        testobj_1_string = u'@'.join((testobj_1.VERSION_PREFIX, test_id_1_loc))
        self.assertEqual(testobj_1._to_string(), testobj_1_string)
        self.assertEqual(str(testobj_1), u'course-v1:' + testobj_1_string)
        self.assertEqual(testobj_1.html_id(), u'course-v1:' + testobj_1_string)
        self.assertEqual(testobj_1.version, test_id_1)

        # Test using a given string
        test_id_2_loc = '519665f6223ebd6980884f2b'
        test_id_2 = ObjectId(test_id_2_loc)
        testobj_2 = CourseLocator(version_guid=test_id_2)
        self.check_course_locn_fields(testobj_2, version_guid=test_id_2)
        self.assertEqual(str(testobj_2.version_guid), test_id_2_loc)

        testobj_2_string = u'@'.join((testobj_2.VERSION_PREFIX, test_id_2_loc))
        self.assertEqual(testobj_2._to_string(), testobj_2_string)
        self.assertEqual(str(testobj_2), u'course-v1:' + testobj_2_string)
        self.assertEqual(testobj_2.html_id(), u'course-v1:' + testobj_2_string)
        self.assertEqual(testobj_2.version, test_id_2)

    @ddt.data(
        ' mit.eecs',
        'mit.eecs ',
        CourseLocator.VERSION_PREFIX + '@mit.eecs',
        BlockUsageLocator.BLOCK_PREFIX + '@black+mit.eecs',
        'mit.ee cs',
        'mit.ee,cs',
        'mit.ee+cs',
        'mit.ee&cs',
        'mit.ee()cs',
        CourseLocator.BRANCH_PREFIX + '@this',
        'mit.eecs+' + CourseLocator.BRANCH_PREFIX,
        'mit.eecs+' + CourseLocator.BRANCH_PREFIX + '@this+' + CourseLocator.BRANCH_PREFIX + '@that',
        'mit.eecs+' + CourseLocator.BRANCH_PREFIX + '@this+' + CourseLocator.BRANCH_PREFIX,
        'mit.eecs+' + CourseLocator.BRANCH_PREFIX + '@this ',
        'mit.eecs+' + CourseLocator.BRANCH_PREFIX + '@th%is ',
        u'\ufffd',
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
            CourseLocator(org='test', course='test', run=bad_id)

        with self.assertRaises(InvalidKeyError):
            CourseKey.from_string(u'course-v1:test+{}+2014_T2'.format(bad_id))

    @ddt.data(
        'course-v1:',
        'course-v1:/mit.eecs',
        'http:mit.eecs',
        'course-v1:mit+course+run{}@branch'.format(CourseLocator.BRANCH_PREFIX),
        'course-v1:mit+course+run+',
    )
    def test_course_constructor_bad_url(self, bad_url):
        with self.assertRaises(InvalidKeyError):
            CourseKey.from_string(bad_url)

    @ddt.data(*itertools.product(
        (
            'course-v1:mit+course+run{}',
            'course-v1:mit+course+run+branch@published{}',
            'course-v1:mit+course+run+branch@published+version@519665f6223ebd6980884f2b{}',
        ),
        ('\n', '\n\n', ' ', '   ', '   \n'),
    ))
    @ddt.unpack
    def test_course_constructor_trailing_whitespace(self, url_with_whitespace_fmt, whitespace):
        with self.assertRaises(InvalidKeyError):
            CourseKey.from_string(url_with_whitespace_fmt.format(whitespace))

    def test_course_constructor_url(self):
        # Test parsing a url when it starts with a version ID and there is also a block ID.
        # This hits the parsers parse_guid method.
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = CourseKey.from_string("course-v1:{}@{}+{}@hw3".format(
            CourseLocator.VERSION_PREFIX, test_id_loc, CourseLocator.BLOCK_PREFIX
        ))
        self.check_course_locn_fields(
            testobj,
            version_guid=ObjectId(test_id_loc)
        )

    def test_course_constructor_url_package_id_and_version_guid(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = CourseKey.from_string(
            'course-v1:mit.eecs+honors.6002x+2014_T2+{}@{}'.format(CourseLocator.VERSION_PREFIX, test_id_loc)
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
        testobj = CourseKey.from_string('course-v1:{}+{}+{}+{}@draft-1+{}@{}'.format(
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
        expected_urn = '{}+{}+{}+{}@{}'.format(org, course, run, CourseLocator.BRANCH_PREFIX, test_branch)
        testobj = CourseLocator(org=org, course=course, run=run, branch=test_branch)
        self.check_course_locn_fields(
            testobj,
            org=org,
            course=course,
            run=run,
            branch=test_branch,
        )

        # pylint: disable=no-member,protected-access
        self.assertEqual(testobj.branch, test_branch)
        self.assertEqual(testobj._to_string(), expected_urn)

    def test_course_constructor_deprecated_offering(self):
        org = 'mit.eecs'
        course = '6002x'
        run = '2014_T2'
        offering = '{}/{}'.format(course, run)
        test_branch = 'published'
        with self.assertDeprecationWarning(count=2):
            testobj = CourseLocator(org=org, offering=offering, branch=test_branch)
            with self.assertRaises(InvalidKeyError):
                CourseLocator(org=org, offering='', branch=test_branch)
            with self.assertRaises(InvalidKeyError):
                CourseLocator(org=org, offering=course, branch=test_branch)
        self.check_course_locn_fields(
            testobj,
            org=org,
            course=course,
            run=run,
            branch=test_branch,
        )

    @ddt.data(
        "i4x://org/course/category/name",
        "i4x://org/course/category/name@revision"
    )
    def test_make_usage_key_from_deprecated_string_roundtrip(self, url):
        course_key = CourseLocator('org', 'course', 'run')
        with self.assertDeprecationWarning(count=2):
            self.assertEqual(
                url,
                course_key.make_usage_key_from_deprecated_string(url).to_deprecated_string()
            )

    def test_empty_run(self):
        with self.assertRaises(InvalidKeyError):
            CourseLocator('org', 'course', '')

        self.assertEqual(
            'org/course/',
            text_type(CourseLocator('org', 'course', '', deprecated=True))
        )

    def test_make_course_key_v2(self):
        """
        Verify that the method `make_course_key_v2` of class `CourseLocator`
        returns a course key v2 object without course run information.
        """
        organization = 'org'
        course_number = 'course'
        course_run = 'run'
        course_run_key = CourseLocator(org=organization, course=course_number, run=course_run)
        expected_course_key_v2 = CourseLocatorV2(org=organization, course=course_number)
        self.assertEqual(expected_course_key_v2, course_run_key.make_course_key_v2())
