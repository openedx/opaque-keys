"""
Compat shim for opaque_keys.edx.asides.

Re-exports AsideDefinitionKeyV1/V2 and AsideUsageKeyV1/V2 from openedx_keys.
All helper functions (_encode_v1, _decode_v1, etc.) are also re-exported for
any downstream code that imports them directly.
"""
from openedx_keys.impl.definitions import (  # noqa: F401
    AsideDefinitionKeyV1,
    AsideDefinitionKeyV2,
)
from openedx_keys.impl.usages import (  # noqa: F401
    AsideUsageKeyV1,
    AsideUsageKeyV2,
    _decode_v1,
    _decode_v2,
    _encode_v1,
    _encode_v2,
    _join_keys_v1,
    _join_keys_v2,
    _split_keys_v1,
    _split_keys_v2,
)
