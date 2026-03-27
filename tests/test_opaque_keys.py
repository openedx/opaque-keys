"""
Tests of basic opaque key functionality, including from_string -> to_string
roundtripping.
"""
import copy
import json
import pickle
from unittest import TestCase

from opaque_keys import OpaqueKey, InvalidKeyError

from test_utils.test_keys import (  # noqa: F401  (imported for class identity match with entry_points)
    DummyKey,
    HexKey,
    HexKeyTwoFields,
    Base10Key,
    DictKey,
)


class KeyTests(TestCase):
    """Basic namespace, from_string, and to_string tests."""
    def test_namespace_from_string(self):
        hex_key = DummyKey.from_string('hex:0x10')
        self.assertIsInstance(hex_key, HexKey)
        self.assertEqual(hex_key.value, 16)
        self.assertEqual(hex_key._to_string(), '0x10')  # pylint: disable=protected-access
        self.assertEqual(len(hex_key), len('hex:0x10'))

        base_key = DummyKey.from_string('base10:15')
        self.assertIsInstance(base_key, Base10Key)
        self.assertEqual(base_key.value, 15)
        self.assertEqual(base_key._to_string(), '15')  # pylint: disable=protected-access
        self.assertEqual(len(base_key), len('base10:15'))

        dict_key = DummyKey.from_string('dict:{"foo": "bar"}')
        self.assertIsInstance(dict_key, DictKey)
        self.assertEqual(dict_key.value, {"foo": "bar"})
        self.assertEqual(dict_key._to_string(), '{"foo": "bar"}')  # pylint: disable=protected-access
        self.assertEqual(len(dict_key), len('dict:{"foo": "bar"}'))

    def test_bad_keys(self):
        with self.assertRaises(InvalidKeyError):
            DummyKey.from_string('hex:10')

        with self.assertRaises(InvalidKeyError):
            DummyKey.from_string('hex:0xZZ')

        with self.assertRaises(InvalidKeyError):
            DummyKey.from_string('base10:0x10')

        with self.assertRaises(InvalidKeyError):
            DummyKey.from_string('dict:abcd')

        with self.assertRaises(InvalidKeyError):
            DummyKey.from_string('\xfb:abcd')

    def test_unknown_namespace(self):
        with self.assertRaises(InvalidKeyError):
            DummyKey.from_string('no_namespace:0x10')

    def test_no_namespace_from_string(self):
        with self.assertRaises(InvalidKeyError):
            DummyKey.from_string('0x10')

        with self.assertRaises(InvalidKeyError):
            DummyKey.from_string('15')

        with self.assertRaises(InvalidKeyError):
            DummyKey.from_string(None)

    def test_immutability(self):
        key = HexKey(10)

        with self.assertRaises(AttributeError):
            key.value = 11  # pylint: disable=attribute-defined-outside-init

        with self.assertRaises(AttributeError):
            del key.value

    def test_equality(self):
        self.assertEqual(DummyKey.from_string('hex:0x10'), DummyKey.from_string('hex:0x10'))
        self.assertNotEqual(DummyKey.from_string('hex:0x10'), DummyKey.from_string('base10:16'))

    def test_hash_equality(self):
        self.assertEqual(hash(DummyKey.from_string('hex:0x10')), hash(DummyKey.from_string('hex:0x10')))
        self.assertNotEqual(hash(DummyKey.from_string('hex:0x10')), hash(DummyKey.from_string('base10:16')))

    def test_constructor(self):
        with self.assertRaises(TypeError):
            HexKey()

        with self.assertRaises(TypeError):
            HexKey(foo='bar')

        with self.assertRaises(TypeError):
            HexKey(10, 20)

        with self.assertRaises(TypeError):
            HexKey(value=10, bar=20)

        with self.assertRaises(TypeError):
            HexKeyTwoFields(10, value=10)

        self.assertEqual(HexKey(10).value, 10)
        self.assertEqual(HexKey(value=10).value, 10)

    def test_replace(self):
        hex10 = HexKey(10)
        hex11 = hex10.replace(value=11)
        hex_copy = hex10.replace()

        self.assertNotEqual(id(hex10), id(hex11))
        self.assertEqual(id(hex10), id(hex_copy))
        self.assertNotEqual(hex10, hex11)
        self.assertEqual(hex10, hex_copy)
        self.assertEqual(HexKey(10), hex10)
        self.assertEqual(HexKey(11), hex11)

    def test_replace_deprecated_property(self):
        deprecated_hex10 = HexKey(10, deprecated=True)
        deprecated_hex11 = deprecated_hex10.replace(value=11)
        not_deprecated_hex10 = deprecated_hex10.replace(deprecated=False)
        deprecated_hex10_copy = deprecated_hex10.replace()

        self.assertNotEqual(deprecated_hex10, deprecated_hex11)
        self.assertEqual(deprecated_hex10, deprecated_hex10_copy)
        self.assertNotEqual(HexKey(10), deprecated_hex10)
        self.assertNotEqual(HexKey(11), deprecated_hex11)
        self.assertEqual(HexKey(10, deprecated=False), not_deprecated_hex10)

        self.assertTrue(deprecated_hex11.deprecated)
        self.assertTrue(deprecated_hex10_copy.deprecated)
        self.assertFalse(not_deprecated_hex10.deprecated)

    def test_copy(self):
        original = DictKey({'foo': 'bar'})
        copied = copy.copy(original)
        deep = copy.deepcopy(original)

        self.assertEqual(original, copied)
        self.assertEqual(id(original), id(copied))
        # For some reason, pylint doesn't think DictKey has a `value` attribute
        self.assertEqual(id(original.value), id(copied.value))  # pylint: disable=no-member

        self.assertEqual(original, deep)
        self.assertEqual(id(original), id(deep))
        self.assertEqual(id(original.value), id(deep.value))  # pylint: disable=no-member

        self.assertEqual(copy.deepcopy([original]), [original])

    def test_subclass(self):
        with self.assertRaises(InvalidKeyError):
            HexKey.from_string('base10:15')

        with self.assertRaises(InvalidKeyError):
            Base10Key.from_string('hex:0x10')

    def test_ordering(self):
        ten = HexKey(value=10)
        eleven = HexKey(value=11)

        self.assertLess(ten, eleven)
        self.assertLessEqual(ten, ten)
        self.assertLessEqual(ten, eleven)
        self.assertGreater(eleven, ten)
        self.assertGreaterEqual(eleven, eleven)
        self.assertGreaterEqual(eleven, ten)

    def test_non_ordering(self):
        # Verify that different key types aren't comparable
        ten = HexKey(value=10)
        twelve = Base10Key(value=12)

        # pylint: disable=pointless-statement
        with self.assertRaises(TypeError):
            ten < twelve

        with self.assertRaises(TypeError):
            ten > twelve

        with self.assertRaises(TypeError):
            ten <= twelve

        with self.assertRaises(TypeError):
            ten >= twelve

    def test_fallback(self):
        # Verify we cannot set more than one deprecated fallback option
        DictKey.set_deprecated_fallback(Base10Key)

        with self.assertRaises(AttributeError):
            DictKey.set_deprecated_fallback(HexKey)

    def test_pickle(self):
        ten = HexKey(value=10)
        deprecated_hex10 = ten.replace(deprecated=True)
        dec_ten = Base10Key(value=10)

        self.assertEqual(ten, pickle.loads(pickle.dumps(ten)))
        self.assertEqual(deprecated_hex10, pickle.loads(pickle.dumps(deprecated_hex10)))
        self.assertEqual(dec_ten, pickle.loads(pickle.dumps(dec_ten)))
