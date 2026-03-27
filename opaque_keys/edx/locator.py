"""
Compat shim for opaque_keys.edx.locator.

All concrete classes are re-exported from openedx_keys (via __getattr__ so
that DeprecationWarnings are emitted on access).  Utility classes LocalId and
CheckFieldMixin are re-exported directly.  Unknown names raise ImportError.
"""
import warnings

from openedx_keys.api import (  # noqa: F401
    LocalId,
    CheckFieldMixin,
    CourseRunKey as _CourseRunKey,
    LegacyLibraryKey as _LegacyLibraryKey,
    LibraryKey as _LibraryKey,
    CourseRunUsageKey as _CourseRunUsageKey,
    LegacyLibraryUsageKey as _LegacyLibraryUsageKey,
    LibraryUsageKey as _LibraryUsageKey,
    CourseRunAssetKey as _CourseRunAssetKey,
    CourseRunDefinitionKey as _CourseRunDefinitionKey,
    CollectionKey as _CollectionKey,
    LibraryContainerKey as _LibraryContainerKey,
    CourselikeUsageKey as _CourselikeUsageKey,
)
from openedx_keys.legacy_api import (  # noqa: F401
    VersionTree,
    BundleDefinitionLocator,
)

_ALIASES = {
    'CourseLocator': _CourseRunKey,
    'LibraryLocator': _LegacyLibraryKey,
    'LibraryLocatorV2': _LibraryKey,
    'BlockUsageLocator': _CourseRunUsageKey,
    'LibraryUsageLocator': _LegacyLibraryUsageKey,
    'LibraryUsageLocatorV2': _LibraryUsageKey,
    'AssetLocator': _CourseRunAssetKey,
    'DefinitionLocator': _CourseRunDefinitionKey,
    'LibraryCollectionLocator': _CollectionKey,
    'LibraryContainerLocator': _LibraryContainerKey,
    # Abstract bases merged into CourselikeUsageKey
    'Locator': _CourselikeUsageKey,
    'BlockLocatorBase': _CourselikeUsageKey,
}


def __getattr__(name):
    if name in _ALIASES:
        new_cls = _ALIASES[name]
        warnings.warn(
            f"{name} is deprecated; use {new_cls.__name__} from openedx_keys instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return new_cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
