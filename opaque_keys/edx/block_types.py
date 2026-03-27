"""
Compat shim for opaque_keys.edx.block_types.

Re-exports BlockTypeKeyV1 from openedx_keys.legacy_api.
set_deprecated_fallback is already called in legacy_api at import time;
we must NOT call it again here or OpaqueKey will raise an error.
"""
from openedx_keys.legacy_api import (  # noqa: F401  pylint: disable=unused-import
    BlockTypeKeyV1,
    XBLOCK_V1,
    XMODULE_V1,
)
