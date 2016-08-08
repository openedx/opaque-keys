"""Test the opaque key utility functions."""

from unittest import TestCase

from opaque_keys.edx.locator import CourseLocator
from opaque_keys.edx.util import get_filename_safe_course_id


VALID_COURSE_ID = u'{}'.format(CourseLocator(org='org', course='course_id', run='course_run'))
VALID_LEGACY_COURSE_ID = "org/course_id/course_run"
INVALID_LEGACY_COURSE_ID = "org:course_id:course_run"
INVALID_NONASCII_LEGACY_COURSE_ID = u"org/course\ufffd_id/course_run"
VALID_NONASCII_LEGACY_COURSE_ID = u"org/cours\u00e9_id/course_run"


class UtilityTests(TestCase):
    """Tests the methods in the util module."""

    def test_get_safe_filename(self):
        self.assertEqual(get_filename_safe_course_id(VALID_COURSE_ID), "org_course_id_course_run")
        self.assertEqual(get_filename_safe_course_id(VALID_COURSE_ID, '-'), "org-course_id-course_run")

    def test_get_filename_with_colon(self):
        course_id = u'{}'.format(CourseLocator(org='org', course='course:id', run='course:run'))
        self.assertEqual(get_filename_safe_course_id(VALID_COURSE_ID), "org_course_id_course_run")
        self.assertEqual(get_filename_safe_course_id(course_id, '-'), "org-course-id-course-run")

    def test_get_filename_for_legacy_id(self):
        self.assertEqual(
            get_filename_safe_course_id(VALID_LEGACY_COURSE_ID),
            "org_course_id_course_run"
        )
        self.assertEqual(
            get_filename_safe_course_id(VALID_LEGACY_COURSE_ID, '-'),
            "org-course_id-course_run"
        )

    def test_get_filename_for_invalid_id(self):
        self.assertEqual(
            get_filename_safe_course_id(INVALID_LEGACY_COURSE_ID),
            "org_course_id_course_run"
        )
        self.assertEqual(
            get_filename_safe_course_id(INVALID_LEGACY_COURSE_ID, '-'),
            "org-course_id-course_run"
        )

    def test_get_filename_for_nonascii_id(self):
        # VALID_NONASCII_LEGACY_COURSE_ID contains an alphanumeric unicode character,
        # so it does not get replaced.
        self.assertEqual(
            get_filename_safe_course_id(VALID_NONASCII_LEGACY_COURSE_ID),
            u"org_cours\u00e9_id_course_run"
        )
        self.assertEqual(
            get_filename_safe_course_id(VALID_NONASCII_LEGACY_COURSE_ID, '-'),
            u"org-cours\u00e9_id-course_run"
        )
        self.assertEqual(
            get_filename_safe_course_id(VALID_NONASCII_LEGACY_COURSE_ID, u'\u00B6'),
            u"org\u00B6cours\u00e9_id\u00B6course_run"
        )
        # INVALID_NONASCII_LEGACY_COURSE_ID contains a non-alphanimeric unicode character,
        # so it gets replaced.
        self.assertEqual(
            get_filename_safe_course_id(INVALID_NONASCII_LEGACY_COURSE_ID),
            u"org_course__id_course_run"
        )
        self.assertEqual(
            get_filename_safe_course_id(INVALID_NONASCII_LEGACY_COURSE_ID, '-'),
            u"org-course-_id-course_run"
        )
        self.assertEqual(
            get_filename_safe_course_id(INVALID_NONASCII_LEGACY_COURSE_ID, u'\u00B6'),
            u"org\u00B6course\u00B6_id\u00B6course_run"
        )
