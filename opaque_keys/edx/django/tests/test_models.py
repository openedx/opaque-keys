"""
Tests the functionality of django.models.
"""

try:
    from django.test import TestCase
    from django.core.exceptions import ValidationError
except ImportError:  # pragma: no cover
    TestCase = object

from unittest import mock
import pytest

from opaque_keys.edx.django.models import OpaqueKeyField, UsageKeyField
from opaque_keys.edx.keys import CollectionKey, ContainerKey, CourseKey, UsageKey

from .models import ComplexModel, Container, ExampleModel


#  pylint: disable=unused-argument
@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable DB access for all tests."""


class TestCreatorMixin(TestCase):
    """Tests of the CreatorMixin class."""
    def setUp(self):
        super().setUp()
        self.model = ExampleModel(key='key-1')
        self.model.save()

    def test_char_field_is_converted_to_container(self):
        expected = Container('key-1').transform()
        self.assertEqual(expected, self.model.key.transform())

    def test_load_model_from_db(self):
        fetched_model = ExampleModel.objects.get(key='key-1')
        self.assertEqual(fetched_model, self.model)


class EmptyKeyClassField(OpaqueKeyField):
    """An invalid class."""


# pylint: disable=protected-access
class TestOpaqueKeyField(TestCase):
    """Tests the implementation of OpaqueKeyField methods."""
    def test_null_key_class_raises_value_error(self):
        with self.assertRaises(AttributeError):
            EmptyKeyClassField()  # AttributeError: 'EmptyKeyClassField' object has no attribute 'KEY_CLASS'

    def test_to_python_trailing_newline_stripped(self):
        field = ComplexModel()._meta.get_field('course_key')
        expected = CourseKey.from_string('course-v1:edX+FUN101x+3T2017')
        self.assertEqual(expected, field.to_python('course-v1:edX+FUN101x+3T2017\n'))

    def test_get_prep_value_newline_not_modified(self):
        field = ComplexModel()._meta.get_field('course_key')
        course_key = mock.MagicMock(spec=CourseKey)
        course_key.__str__.return_value = 'course-v1:edX+FUN101x+3T2017\n'
        self.assertEqual('course-v1:edX+FUN101x+3T2017\n', field.get_prep_value(course_key))


class TestKeyFieldImplementation(TestCase):
    """Tests for all of the subclasses of OpaqueKeyField."""
    def setUp(self):
        super().setUp()
        self.course_key = CourseKey.from_string('course-v1:edX+FUN101x+3T2017')
        self.usage_key = UsageKey.from_string('block-v1:edX+FUN101x+3T2017+type@html+block@12345678')
        self.collection_key = CollectionKey.from_string('lib-collection:TestX:LibraryX:test-problem-bank')
        self.container_key = ContainerKey.from_string('lct:TestX:LibraryX:unit:test-container')
        self.model = ComplexModel(
            id='foobar',
            course_key=self.course_key,
            course_key_cs=self.course_key,
            usage_key=self.usage_key,
            collection_key=self.collection_key,
            container_key=self.container_key,
        )
        self.model.save()

    def tearDown(self):
        super().tearDown()
        self.model.delete()

    def test_fetch_from_db(self):
        fetched = ComplexModel.objects.filter(course_key=self.course_key).first()
        self.assertEqual(fetched, self.model)

    def test_fetch_from_db_with_str(self):
        fetched = ComplexModel.objects.filter(course_key=str(self.course_key)).first()
        self.assertEqual(fetched, self.model)

    def test_fetch_from_db_with_str_case_insensitive(self):
        """Fetching keys should be case-insensitive by default for backwards compatibility"""
        assert str(self.course_key).lower() != str(self.course_key)
        fetched = ComplexModel.objects.get(course_key=str(self.course_key).lower())
        assert str(fetched.course_key) == str(self.model.course_key)  # fetched has the correct capitalization though

    def test_fetch_from_db_with_str_case_sensitive(self):
        """Fetching keys should be case-sensitive when case_sensitive=True"""
        assert str(self.course_key).lower() != str(self.course_key)
        with self.assertRaises(ComplexModel.DoesNotExist):
            ComplexModel.objects.get(course_key_cs=str(self.course_key).lower())
        # But this works:
        fetched = ComplexModel.objects.get(course_key_cs=str(self.course_key))
        assert fetched.course_key == self.course_key

    def test_custom_max_length(self):
        """
        Test that fields can override max_length to be different from the default of 255
        """
        key_100 = CourseKey.from_string(
            "course-v1:fiftyfiftyfiftyfiftyfiftyfiftyfiftyfiftyfiftyfifty+thishasten+twenty-eight-more-characters",
        )
        key_101 = CourseKey.from_string(
            "course-v1:fiftyfiftyfiftyfiftyfiftyfiftyfiftyfiftyfiftyfifty+thishasten+twenty-eight-more-charactersX",
        )
        # Note that ComplexModel.course_key_cs specifies max_length=100. So this should work:
        assert len(str(key_100)) == 100
        self.model.course_key_cs = key_100
        self.model.full_clean()
        # But this should fail:
        assert len(str(key_101)) == 101
        self.model.course_key_cs = key_101
        with self.assertRaises(ValidationError):
            self.model.full_clean()
        # Note: we do not test the actual database constraints on length, because SQLite does not enforce it.
        # But the Django validation above reflects the same limits, and MySQL should enforce them.

    def test_validation_no_errors(self):
        self.model.clean_fields()

    def test_validation_custom_validator_raises_error(self):
        with self.assertRaises(ValidationError):
            self.model.course_key = CourseKey.from_string('course-v1:NOTedX+FUN101x+3T2017')
            self.model.clean_fields()

    def test_validation_blank_usage_key_raises_error(self):
        with self.assertRaises(ValidationError):
            self.model.usage_key = UsageKeyField.Empty
            self.model.clean_fields()
