"""Utility functions for opaque keys."""
import re

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey


def get_filename_safe_course_id(course_id, replacement_char='_'):
    """
    Create a representation of a course_id that can be used safely in a filepath.
    """
    try:
        course_key = CourseKey.from_string(course_id)
        filename = replacement_char.join([course_key.org, course_key.course, course_key.run])
    except InvalidKeyError:
        # If the course_id doesn't parse, we will still return a value here.
        filename = course_id

    # The safest characters are A-Z, a-z, 0-9, <underscore>, <period> and <hyphen>.
    # We represent the first four with \w and the re.UNICODE flag, which covers
    # ASCII and unicode alphanumeric characters.
    return re.sub(r'[^\w\.\-]', replacement_char, filename, flags=re.UNICODE)
