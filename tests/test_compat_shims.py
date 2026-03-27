"""
Tests for the opaque_keys.edx.* compat shims.

Verifies:
1. Old names in locator.py emit DeprecationWarning on access
2. Those names resolve to the correct new classes
3. isinstance/issubclass checks work through the shims
4. Never-existed names raise ImportError (from-import) or AttributeError (getattr)
5. Direct re-exports in keys.py, asides.py, block_types.py, locations.py work without warnings
"""
import importlib
import warnings
from unittest import TestCase

import opaque_keys.edx.locator as locator_shim
from openedx_keys.api import (
    ContextKey,
    CourselikeKey,
    CourseRunKey,
    LegacyLibraryKey,
    LibraryKey,
    CourseRunUsageKey,
    LegacyLibraryUsageKey,
    LibraryUsageKey,
    CourseRunAssetKey,
    CourseRunDefinitionKey,
    CollectionKey,
    LibraryContainerKey,
    ContentUsageKey,
    UsageKey,
    AssetKey,
    DefinitionKey,
    ContainerKey,
    AsideDefinitionKey,
    AsideUsageKey,
)


class TestLocatorShimDeprecatedNames(TestCase):
    """opaque_keys.edx.locator: __getattr__-dispatched names emit DeprecationWarning."""

    _DEPRECATED = [
        ('CourseLocator', CourseRunKey),
        ('LibraryLocator', LegacyLibraryKey),
        ('LibraryLocatorV2', LibraryKey),
        ('BlockUsageLocator', CourseRunUsageKey),
        ('LibraryUsageLocator', LegacyLibraryUsageKey),
        ('LibraryUsageLocatorV2', LibraryUsageKey),
        ('AssetLocator', CourseRunAssetKey),
        ('DefinitionLocator', CourseRunDefinitionKey),
        ('LibraryCollectionLocator', CollectionKey),
        ('LibraryContainerLocator', LibraryContainerKey),
        ('Locator', None),         # abstract alias
        ('BlockLocatorBase', None),  # abstract alias
    ]

    def _get_with_warning_check(self, name):
        """Return (cls, warnings_list) after accessing locator_shim.<name>."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', DeprecationWarning)
            cls = getattr(locator_shim, name)
        deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        return cls, deprecations

    def test_deprecated_names_warn(self):
        for name, _ in self._DEPRECATED:
            with self.subTest(name=name):
                _, deprecations = self._get_with_warning_check(name)
                self.assertEqual(
                    len(deprecations), 1,
                    f"Expected exactly 1 DeprecationWarning for {name}, got {len(deprecations)}"
                )

    def test_deprecated_names_resolve_to_correct_class(self):
        for name, expected_cls in self._DEPRECATED:
            if expected_cls is None:
                continue
            with self.subTest(name=name):
                cls, _ = self._get_with_warning_check(name)
                self.assertIs(
                    cls, expected_cls,
                    f"{name} should resolve to {expected_cls.__name__}, got {cls.__name__}"
                )

    def test_deprecated_warning_message_mentions_old_and_new_name(self):
        cls, deprecations = self._get_with_warning_check('CourseLocator')
        msg = str(deprecations[0].message)
        self.assertIn('CourseLocator', msg)
        self.assertIn('CourseRunKey', msg)

    def test_never_existed_name_raises_attribute_error_via_getattr(self):
        with self.assertRaises(AttributeError):
            getattr(locator_shim, 'TotallyMadeUpClass')

    def test_never_existed_name_raises_import_error_via_from_import(self):
        with self.assertRaises(ImportError):
            # Dynamically run a from-import to trigger ImportError conversion
            importlib.import_module('opaque_keys.edx.locator')
            exec("from opaque_keys.edx.locator import TotallyMadeUpClass")  # pylint: disable=exec-used


class TestLocatorShimDirectExports(TestCase):
    """opaque_keys.edx.locator: directly re-exported names don't warn."""

    def test_local_id_importable_without_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', DeprecationWarning)
            from opaque_keys.edx.locator import LocalId  # noqa: F401
        deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        self.assertEqual(deprecations, [])

    def test_check_field_mixin_importable_without_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', DeprecationWarning)
            from opaque_keys.edx.locator import CheckFieldMixin  # noqa: F401
        deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        self.assertEqual(deprecations, [])

    def test_version_tree_importable(self):
        from opaque_keys.edx.locator import VersionTree  # noqa: F401

    def test_bundle_definition_locator_importable(self):
        from opaque_keys.edx.locator import BundleDefinitionLocator  # noqa: F401


class TestKeysShimDirectExports(TestCase):
    """opaque_keys.edx.keys: direct re-exports work and resolve to correct new types."""

    def test_course_key_is_courselike_key(self):
        from opaque_keys.edx.keys import CourseKey
        self.assertIs(CourseKey, CourselikeKey)

    def test_learning_context_key_is_context_key(self):
        from opaque_keys.edx.keys import LearningContextKey
        self.assertIs(LearningContextKey, ContextKey)

    def test_usage_key_v2_is_content_usage_key(self):
        from opaque_keys.edx.keys import UsageKeyV2
        self.assertIs(UsageKeyV2, ContentUsageKey)

    def test_usage_key_importable(self):
        from opaque_keys.edx.keys import UsageKey as UK
        self.assertIs(UK, UsageKey)

    def test_asset_key_importable(self):
        from opaque_keys.edx.keys import AssetKey as AK
        self.assertIs(AK, AssetKey)

    def test_definition_key_importable(self):
        from opaque_keys.edx.keys import DefinitionKey as DK
        self.assertIs(DK, DefinitionKey)

    def test_container_key_importable(self):
        from opaque_keys.edx.keys import ContainerKey as CK
        self.assertIs(CK, ContainerKey)

    def test_aside_definition_key_importable(self):
        from opaque_keys.edx.keys import AsideDefinitionKey as ADK
        self.assertIs(ADK, AsideDefinitionKey)

    def test_aside_usage_key_importable(self):
        from opaque_keys.edx.keys import AsideUsageKey as AUK
        self.assertIs(AUK, AsideUsageKey)

    def test_isinstance_check_via_course_key(self):
        """isinstance(course_run_key, CourseKey) must work through the shim."""
        from opaque_keys.edx.keys import CourseKey
        key = CourseRunKey.from_string('course-v1:org+course+run')
        self.assertIsInstance(key, CourseKey)

    def test_isinstance_check_via_usage_key(self):
        from opaque_keys.edx.keys import UsageKey as UK
        key = CourseRunUsageKey.from_string('block-v1:org+course+run+type@html+block@abc')
        self.assertIsInstance(key, UK)

    def test_no_deprecation_warnings_on_import(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', DeprecationWarning)
            importlib.reload(importlib.import_module('opaque_keys.edx.keys'))
        deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        self.assertEqual(deprecations, [])


class TestAsidesShimDirectExports(TestCase):
    """opaque_keys.edx.asides: re-exports are importable without DeprecationWarning."""

    def test_aside_keys_importable(self):
        from opaque_keys.edx.asides import (  # noqa: F401
            AsideDefinitionKeyV1,
            AsideDefinitionKeyV2,
            AsideUsageKeyV1,
            AsideUsageKeyV2,
        )

    def test_encode_decode_helpers_importable(self):
        from opaque_keys.edx.asides import (  # noqa: F401
            _encode_v1, _decode_v1, _encode_v2, _decode_v2,
        )

    def test_no_deprecation_warnings_on_import(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', DeprecationWarning)
            importlib.reload(importlib.import_module('opaque_keys.edx.asides'))
        deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        self.assertEqual(deprecations, [])


class TestBlockTypesShimDirectExports(TestCase):
    """opaque_keys.edx.block_types: re-exports are importable without DeprecationWarning."""

    def test_block_type_key_v1_importable(self):
        from opaque_keys.edx.block_types import BlockTypeKeyV1  # noqa: F401

    def test_constants_importable(self):
        from opaque_keys.edx.block_types import XBLOCK_V1, XMODULE_V1  # noqa: F401


class TestLocationsShimDirectExports(TestCase):
    """opaque_keys.edx.locations: re-exports are importable without DeprecationWarning."""

    def test_location_classes_importable(self):
        from opaque_keys.edx.locations import (  # noqa: F401
            SlashSeparatedCourseKey,
            LocationBase,
            Location,
            DeprecatedLocation,
            AssetLocation,
        )

    def test_i4x_encoder_importable(self):
        from opaque_keys.edx.locations import i4xEncoder  # noqa: F401
