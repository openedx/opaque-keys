"""
Compat shim for opaque_keys.edx.locations.

Re-exports all location-related classes from openedx_keys.legacy_api.
"""
from openedx_keys.legacy_api import (  # noqa: F401
    i4xEncoder,
    SlashSeparatedCourseKey,
    LocationBase,
    Location,
    DeprecatedLocation,
    AssetLocation,
)
