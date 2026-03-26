"""
Compat shim for opaque_keys.edx.keys.

All public names are re-exported from openedx_keys.api (or legacy_api) so
that existing code importing from here continues to work.  Abstract base
classes are re-exported directly (not via __getattr__) so that
isinstance/issubclass checks and stevedore's check_func pass correctly.
"""
import warnings

# ---------------------------------------------------------------------------
# Direct re-exports of abstract bases (renamed ones become the same object as
# the new name, so issubclass checks work without changes in downstream code).
# ---------------------------------------------------------------------------
from openedx_keys.api import (  # noqa: F401
    ContextKey as LearningContextKey,
    CourselikeKey as CourseKey,
    DefinitionKey,
    CourseObjectMixin,
    AssetKey,
    UsageKey,
    ContentUsageKey as UsageKeyV2,
    ContainerKey,
    CollectionKey,
    AsideDefinitionKey,
    AsideUsageKey,
    i4xEncoder,
)
from openedx_keys.legacy_api import BlockTypeKey  # noqa: F401

# ---------------------------------------------------------------------------
# __getattr__ is NOT needed here: every name that used to live in this module
# is either directly re-exported above or was never part of the public API.
# ---------------------------------------------------------------------------
