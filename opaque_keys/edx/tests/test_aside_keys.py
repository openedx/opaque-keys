"""
Tests of AsideUsageKeyV1 and AsideDefinitionKeyV1.
"""

import itertools
from unittest import TestCase

from six import text_type
import ddt

from opaque_keys.edx.asides import AsideUsageKeyV1, AsideDefinitionKeyV1, _encode, _decode
from opaque_keys.edx.keys import AsideUsageKey, AsideDefinitionKey
from opaque_keys.edx.locations import Location
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator, DefinitionLocator


@ddt.ddt
class TestEncode(TestCase):
    """Tests of encoding and decoding functions."""

    @ddt.data(*(''.join(substrs) for substrs in itertools.product(['$', '$$', '::', ':', 'x'], repeat=3)))
    def test_encode_roundtrip(self, data):
        """
        Test all combinations that include characters we're trying to encode, or using in the encoding.

        Use 7 character permutations so that we can test all surrounding contexts for
        characters/strings used in the encoding scheme.
        """
        encoded = _encode(data)
        decoded = _decode(encoded)
        self.assertEqual(data, decoded)


@ddt.ddt
class TestAsideKeys(TestCase):
    """Test of Aside keys."""
    @ddt.data(
        (Location.from_string('i4x://org/course/cat/name'), 'aside'),
        (BlockUsageLocator(CourseLocator('org', 'course', 'run'), 'block_type', 'block_id'), 'aside'),
    )
    @ddt.unpack
    def test_usage_round_trip_deserialized(self, usage_key, aside_type):
        key = AsideUsageKeyV1(usage_key, aside_type)
        serialized = text_type(key)
        deserialized = AsideUsageKey.from_string(serialized)
        self.assertEqual(key, deserialized)
        self.assertEqual(usage_key, key.usage_key, usage_key)
        self.assertEqual(usage_key, deserialized.usage_key)
        self.assertEqual(aside_type, key.aside_type)
        self.assertEqual(aside_type, deserialized.aside_type)

    @ddt.data(
        'aside-usage-v1:i4x://org/course/cat/name::aside',
        'aside-usage-v1:block-v1:org+course+cat+type@block_type+block@name::aside',
    )
    def test_usage_round_trip_serialized(self, aside_key):
        deserialized = AsideUsageKey.from_string(aside_key)
        serialized = text_type(deserialized)
        self.assertEqual(aside_key, serialized)

    @ddt.data(
        (DefinitionLocator('block_type', 'abcd1234abcd1234abcd1234'), 'aside'),
    )
    @ddt.unpack
    def test_definition_round_trip_deserialized(self, definition_key, aside_type):
        key = AsideDefinitionKeyV1(definition_key, aside_type)
        serialized = text_type(key)
        deserialized = AsideDefinitionKey.from_string(serialized)
        self.assertEqual(key, deserialized)
        self.assertEqual(definition_key, key.definition_key, definition_key)
        self.assertEqual(definition_key, deserialized.definition_key)
        self.assertEqual(aside_type, key.aside_type)
        self.assertEqual(aside_type, deserialized.aside_type)

    @ddt.data(
        'aside-def-v1:def-v1:abcd1234abcd1234abcd1234+type@block_type::aside'
    )
    def test_definition_round_trip_serialized(self, aside_key):
        deserialized = AsideDefinitionKey.from_string(aside_key)
        serialized = text_type(deserialized)
        self.assertEqual(aside_key, serialized)

    @ddt.data(
        ('aside_type', 'bside'),
        ('usage_key', BlockUsageLocator(CourseLocator('borg', 'horse', 'gun'), 'lock_type', 'lock_id')),
        ('block_id', 'lock_id'),
        ('block_type', 'lock_type'),
        # BlockUsageLocator can't `replace` a definition_key, so skip for now
        # ('definition_key', DefinitionLocator('block_type', 'abcd1234abcd1234abcd1234')),
        ('course_key', CourseLocator('borg', 'horse', 'gun')),
    )
    @ddt.unpack
    def test_usage_key_replace(self, attr, value):
        key = AsideUsageKeyV1(BlockUsageLocator(CourseLocator('org', 'course', 'run'), 'block_type', 'block_id'),
                              'aside')
        new_key = key.replace(**{attr: value})
        self.assertEqual(getattr(new_key, attr), value)

    @ddt.data(
        ('aside_type', 'bside'),
        ('definition_key', DefinitionLocator('block_type', 'abcd1234abcd1234abcd1234')),
        ('block_type', 'lock_type'),
    )
    @ddt.unpack
    def test_definition_key_replace(self, attr, value):
        key = AsideDefinitionKeyV1(DefinitionLocator('block_type', 'abcd1234abcd1234abcd1234'), 'aside')
        new_key = key.replace(**{attr: value})
        self.assertEqual(getattr(new_key, attr), value)
