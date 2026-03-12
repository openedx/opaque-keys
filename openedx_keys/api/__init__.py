"""
Public, supported API for keys in the Open edX platform.
"""

# pylint: disable=wildcard-import,unused-import

from opaque_keys import (
    InvalidKeyError,
    OpaqueKey,
    # EXCLUDED:
    # OpaqueKeyMetaclass (implementation detail)
)
from opaque_keys.edx.asides import (
    AsideDefinitionKeyV1,
    AsideDefinitionKeyV2,
    AsideUsageKeyV1,
    AsideUsageKeyV2,
)
from opaque_keys.edx.block_types import (
    BlockTypeKeyV1,
    # EXCLUDED:
    # XBLOCK_V1 (unused)
    # XMODULE_V1 (unused and deprecated)
)
from opaque_keys.edx.django.models import (
    BlockTypeKeyField,
    CollectionKeyField,
    ContainerKeyField,
    CourseKeyField,
    LearningContextKeyField,
    UsageKeyField,
    # EXCLUDED
    # CreatorMixin (unused)
    # OpaqueKeyField (unused and silly)
    # OpaqueKeyFieldEmptyLookupIsNull (unused)
    # LocationKeyField (deprecated)
)
from opaque_keys.edx.keys import (
    AsideDefinitionKey,
    AsideUsageKey,
    AssetKey,
    BlockTypeKey,
    ContainerKey,
    LearningContextKey as ContextKey,
    CourseKey as CourselikeKey,
    UsageKey,
    UsageKeyV2 as ContentUsageKey,
    # EXCLUDED:
    # CourseObjectMixin (should be private)
    # CollectionKey (implementation detail of CollectionKeyV2)
    # DefinitionKey (implementation detail of DefinitionKeyV1)
    # i4xEncoder (deprecated)
)
from opaque_keys.edx.locator import (
    LibraryCollectionLocator as CollectionKey,
    AssetLocator as CourseRunAssetKey,
    DefinitionLocator as CourseRunDefinitionKey,
    CourseLocator as CourseRunKey,
    BlockUsageLocator as CourseRunUsageKey,
    LibraryLocator as LegacyLibraryKey,
    LibraryUsageLocator as LecacyLibraryUsageKey,
    LibraryLocatorV2 as LibraryKey,
    LibraryContainerLocator as LibraryContainerKey,
    LibraryUsageLocatorV2 as LibraryUsageKey,
    LocalId,
    # EXCLUDED:
    # BlockLocatorBase (implementation detail)
    # BundleDefinitionLocator (deprecated)
    # CheckFieldMixin (should be private)
    # Locator (implementation detail)
    # VersionTree (unused)
)
# EXCLUDED:
# opaque_keys.edx.location (deprecated)
