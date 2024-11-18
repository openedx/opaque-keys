from django.db import connection

if 'postgresql' in connection.vendor.lower():
    from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
    from psycopg2.extensions import register_adapter, QuotedString


    def adapt_course_locator(course_locator):
        return QuotedString(course_locator._to_string())


    # Register the adapter
    register_adapter(CourseLocator, adapt_course_locator)
