"""
Compat shim for opaque_keys.edx.django.models.

Re-exports all field classes from openedx_keys.api and openedx_keys.legacy_api.
LearningContextKeyField is a deprecated alias for ContextKeyField.
"""
import warnings

from openedx_keys.impl.fields import (  # noqa: F401  pylint: disable=unused-import
    _Creator,
    CreatorMixin,
    OpaqueKeyField,
    OpaqueKeyFieldEmptyLookupIsNull,
    ContextKeyField,
    CourseKeyField,
    UsageKeyField,
    ContainerKeyField,
    CollectionKeyField,
)
from openedx_keys.legacy_api import (  # noqa: F401  pylint: disable=unused-import
    BlockTypeKeyField,
    LocationKeyField,
)


def __getattr__(name):
    if name == 'LearningContextKeyField':
        warnings.warn(
            "LearningContextKeyField is deprecated; use ContextKeyField instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return ContextKeyField
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
