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
    OpaqueKeyField,
    UsageKeyField,
    # EXCLUDED:
    # CreatorMixin (should be private)
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
    CourseKey as ContextKeyV1,
    UsageKey,
    UsageKeyV2,
    # EXCLUDED:
    # CourseObjectMixin (should be private)
    # CollectionKey (implementation detail of CollectionKeyV2)
    # DefinitionKey (implementation detail of DefinitionKeyV1)
    # i4xEncoder (deprecated)
)
from opaque_keys.edx.locator import (
    AssetLocator as AssetKeyV1,
    LibraryCollectionLocator as CollectionKeyV2,
    CourseLocator as CourseKeyV1,
    DefinitionLocator as DefinitionKeyV1,
    LibraryContainerLocator as LibraryContainerKeyV2,
    LibraryLocator as LibraryKeyV1,
    LibraryLocatorV2 as LibraryKeyV2,
    LibraryUsageLocator as LibraryUsageKeyV1,
    LibraryUsageLocatorV2 as LibraryUsageKeyV2,
    LocalId,
    BlockUsageLocator as UsageKeyV1,
    # EXCLUDED:
    # BlockLocatorBase (implementation detail)
    # BundleDefinitionLocator (deprecated)
    # CheckFieldMixin (should be private)
    # Locator (implementation detail)
    # VersionTree (unused)
)
# EXCLUDED:
# opaque_keys.edx.location (deprecated)
