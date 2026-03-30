# V4 Plan

Snapshot of the V4 refactoring plan.
Key changes from V3: domain-oriented `impl/` modules (instead of bases/keys/aside/block_type);
`legacy_api.py` for locations + block_types + deprecated stragglers; aside keys co-located with
their domain module; `i4xEncoder` in `base.py`; `legacy_api.py` is a strict leaf (nothing in
`openedx_keys/` imports from it).

---

## New Package Structure

```
openedx_keys/               # new dir within the opaque-keys repo (same package)
    __init__.py
    api.py                  # public facade: wildcard-imports all impl modules
    legacy_api.py           # leaf module: locations.py + block_types.py + deprecated stragglers
    impl/
        __init__.py
        base.py             # OpaqueKey re-export, CourseObjectMixin, exceptions,
                            #   LocalId, CheckFieldMixin, i4xEncoder
        contexts.py         # ContextKey hierarchy: ContextKey, CourselikeKey,
                            #   CourseRunKey, LegacyLibraryKey, LibraryKey
        usages.py           # UsageKey hierarchy: UsageKey, ContentUsageKey,
                            #   CourselikeUsageKey, CourseRunUsageKey,
                            #   LegacyLibraryUsageKey, LibraryUsageKey,
                            #   AsideUsageKey, AsideUsageKeyV1/V2
        assets.py           # AssetKey, CourseRunAssetKey
        collections.py      # CollectionKey (concrete; absorbs the old abstract)
        containers.py       # ContainerKey, LibraryContainerKey
        definitions.py      # DefinitionKey, CourseRunDefinitionKey,
                            #   AsideDefinitionKey, AsideDefinitionKeyV1/V2
        fields.py           # Django model fields (all except BlockTypeKeyField)

opaque_keys/edx/            # becomes a compat mirror; each module re-exports
    keys.py                 # from openedx_keys.api with old names → deprecation warnings
    locator.py
    asides.py
    block_types.py
    django/
        models.py
    locations.py            # backcompat shims for Location, i4xEncoder, etc.
```

### Dependency rules

- `impl/*` modules may only import from `opaque_keys` (the base package) and from
  other `openedx_keys/impl/` modules that are lower in the list above.
- `api.py` imports from `impl/*` only.
- `legacy_api.py` may import from `openedx_keys.api` (or `impl/*`) but **nothing**
  in `openedx_keys/` imports from `legacy_api.py`.
- `opaque_keys/edx/` compat modules import from `openedx_keys.api` or
  `openedx_keys.legacy_api` as appropriate.

### Contents of `legacy_api.py`

Everything that is either already deprecated or considered legacy and not worth
promoting to the clean API:

- From `locations.py`: `SlashSeparatedCourseKey`, `LocationBase`, `Location`,
  `DeprecatedLocation`, `AssetLocation`
- From `locator.py`: `VersionTree`, `BundleDefinitionLocator`
- From `block_types.py`: `BlockTypeKey` (abstract), `BlockTypeKeyV1`
- From `django/models.py`: `BlockTypeKeyField`, `LocationKeyField` (already
  deprecated alias) — co-located here because their `KEY_CLASS` is in this module

`openedx_keys/api.py` does **not** wildcard-import `legacy_api.py`. Legacy callers
import directly from `openedx_keys.legacy_api` or from the `opaque_keys.edx.*`
compat shims.

### `api.py` structure

```python
from openedx_keys.impl.base import *
from openedx_keys.impl.contexts import *
from openedx_keys.impl.usages import *
from openedx_keys.impl.assets import *
from openedx_keys.impl.collections import *
from openedx_keys.impl.containers import *
from openedx_keys.impl.definitions import *
from openedx_keys.impl.fields import *
```

Each `impl/` module defines `__all__` listing only its public symbols.

### Compat module pattern

```python
# opaque_keys/edx/locator.py
from openedx_keys.api import CourseRunKey as _CourseRunKey, ...

_ALIASES = {"CourseLocator": _CourseRunKey, ...}

def __getattr__(name):
    if name in _ALIASES:
        warnings.warn(f"{name} is deprecated, use {_ALIASES[name].__name__} instead",
                      DeprecationWarning, stacklevel=2)
        return _ALIASES[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

- `from opaque_keys.edx.locator import CourseLocator` → works, emits `DeprecationWarning`
- `from opaque_keys.edx.locator import CourseRunKey` → `AttributeError`

`opaque_keys/edx/locations.py` follows the same pattern; its `i4xEncoder` becomes a
shim pointing to `openedx_keys.api.i4xEncoder`.

---

## Backwards Compatibility Mechanisms

**Class renames:** New class lives in `openedx_keys/impl/`. Compat module exposes old
name via module-level `__getattr__` → `DeprecationWarning`. Old name is the same class
object so `isinstance` checks work unchanged.

**Field/property renames:** Primary storage uses new `_code` name. Old name exposed as
a `@property` that emits `DeprecationWarning` and delegates to new name.

**Constructor kwarg renames:** `__init__` accepts both old and new kwarg names. Old name
emits `DeprecationWarning` and maps to new name. Error if both supplied.

**Django field renames:** Same module-level `__getattr__` pattern in compat
`django/models.py`. `KEY_CLASS` on each field points to the new key class.

**Entry points in setup.py (openedx_keys):** Reference new class names directly (avoids
spurious deprecation warnings on stevedore load).

---

## Intentional Breaking Changes

These are the ONLY breaking changes. Downstream subclasses of the merged-away classes
must update their base class. Document in changelog.

| Merged-away class | Merged into | Downstream impact |
|---|---|---|
| `Locator` (abstract) | `CourselikeUsageKey` (abstract) | Subclasses of `Locator` must change base to `CourselikeUsageKey` |
| `BlockLocatorBase` (abstract) | `CourselikeUsageKey` (abstract) | Subclasses of `BlockLocatorBase` must change base to `CourselikeUsageKey` |
| `CollectionKey` abstract (`keys.py`) | `CollectionKey` concrete (`locator.py`) | Subclasses of the old abstract `CollectionKey` must update |

---

## Part 1: Class Renames

### `impl/base.py`

| Old Name | New Name | Notes |
|---|---|---|
| `CourseObjectMixin` | `CourseObjectMixin` | Unchanged; mixin for course-scoped keys |
| `i4xEncoder` | `i4xEncoder` | Unchanged name; moved from `keys.py` |
| `LocalId` | `LocalId` | Unchanged; moved from `locator.py` |
| `CheckFieldMixin` | `CheckFieldMixin` | Unchanged; internal mixin from `locator.py` |

Exception classes from `opaque_keys` base package re-exported here for convenience.

### `impl/contexts.py` — Context (learning context) key hierarchy

| Old Name | New Name | Notes |
|---|---|---|
| `LearningContextKey` | `ContextKey` | Abstract |
| `CourseKey` | `CourselikeKey` | Abstract; very widely used downstream — compat alias critical |
| `CourseLocator` | `CourseRunKey` | nee `CourseLocator` |
| `LibraryLocator` | `LegacyLibraryKey` | (Archived) nee `LibraryLocator` |
| `LibraryLocatorV2` | `LibraryKey` | nee `LibraryLocatorV2`; clean name, no version suffix |

`CourselikeKey.make_usage_key(block_type, block_id)` → `make_usage_key(type_code, block_code)` (old kwarg names get compat handling).
`CourselikeKey.make_asset_key(asset_type, path)` → `make_asset_key(type_code, path)` (old `asset_type` kwarg gets compat handling; `path` unchanged).

### `impl/usages.py` — Usage key hierarchy

| Old Name | New Name | Notes |
|---|---|---|
| `UsageKey` | `UsageKey` | Abstract; unchanged name |
| `UsageKeyV2` | `ContentUsageKey` | Abstract |
| `Locator` | `CourselikeUsageKey` | Abstract; merged with `BlockLocatorBase` |
| `BlockLocatorBase` | `CourselikeUsageKey` | Abstract; merged with `Locator` |
| `BlockUsageLocator` | `CourseRunUsageKey` | nee `BlockUsageLocator` |
| `LibraryUsageLocator` | `LegacyLibraryUsageKey` | nee `LibraryUsageLocator` |
| `LibraryUsageLocatorV2` | `LibraryUsageKey` | nee `LibraryUsageLocatorV2`; clean name |
| `AsideUsageKey` | `AsideUsageKey` | Abstract; unchanged name |
| `AsideUsageKeyV1` | `AsideUsageKeyV1` | Unchanged name; field renames only |
| `AsideUsageKeyV2` | `AsideUsageKeyV2` | Unchanged name; field renames only |

`CourseRunUsageKey.make_relative(course_locator, block_type, block_id)` → `make_relative(course_locator, type_code, block_code)` (old kwarg names get compat handling).

### `impl/assets.py` — Asset key hierarchy

| Old Name | New Name | Notes |
|---|---|---|
| `AssetKey` | `AssetKey` | Abstract; unchanged name |
| `AssetLocator` | `CourseRunAssetKey` | nee `AssetLocator` |

`CourseRunAssetKey` inherits `type_code` and `block_code` from `CourseRunUsageKey`.
`path` (alias for `block_code`) kept accessible without a deprecation warning — it's descriptive.

### `impl/collections.py` — Collection key hierarchy

| Old Name | New Name | Notes |
|---|---|---|
| `CollectionKey` abstract (`keys.py`) | *(absorbed)* | Merged into the one concrete impl |
| `LibraryCollectionLocator` | `CollectionKey` | Absorbs abstract `CollectionKey` from `keys.py` |

### `impl/containers.py` — Container key hierarchy

| Old Name | New Name | Notes |
|---|---|---|
| `ContainerKey` | `ContainerKey` | Abstract; unchanged name |
| `LibraryContainerLocator` | `LibraryContainerKey` | nee `LibraryContainerLocator` |

### `impl/definitions.py` — Definition key hierarchy

| Old Name | New Name | Notes |
|---|---|---|
| `DefinitionKey` | `DefinitionKey` | Abstract; unchanged name |
| `DefinitionLocator` | `CourseRunDefinitionKey` | nee `DefinitionLocator` |
| `AsideDefinitionKey` | `AsideDefinitionKey` | Abstract; unchanged name |
| `AsideDefinitionKeyV1` | `AsideDefinitionKeyV1` | Unchanged name; field renames only |
| `AsideDefinitionKeyV2` | `AsideDefinitionKeyV2` | Unchanged name; field renames only |

### `impl/fields.py` — Django model fields

| Old Name | New Name | Notes |
|---|---|---|
| `_Creator` | `_Creator` | Internal; unchanged |
| `CreatorMixin` | `CreatorMixin` | Unchanged |
| `OpaqueKeyField` | `OpaqueKeyField` | Unchanged |
| `OpaqueKeyFieldEmptyLookupIsNull` | `OpaqueKeyFieldEmptyLookupIsNull` | Unchanged |
| `LearningContextKeyField` | `ContextKeyField` | `KEY_CLASS` → `ContextKey` |
| `CourseKeyField` | `CourseKeyField` | Unchanged name; `KEY_CLASS` → `CourselikeKey` |
| `UsageKeyField` | `UsageKeyField` | Unchanged |
| `ContainerKeyField` | `ContainerKeyField` | Unchanged |
| `CollectionKeyField` | `CollectionKeyField` | Unchanged name; `KEY_CLASS` → new `CollectionKey` |

### `legacy_api.py` — Legacy and deprecated classes

| Old Name | New Name | Source | Notes |
|---|---|---|---|
| `BlockTypeKey` | `BlockTypeKey` | `keys.py` | Abstract; no clean-API promotion |
| `BlockTypeKeyV1` | `BlockTypeKeyV1` | `block_types.py` | Unchanged |
| `BlockTypeKeyField` | `BlockTypeKeyField` | `django/models.py` | Co-located; `KEY_CLASS` = `BlockTypeKey` |
| `LocationKeyField` | `LocationKeyField` | `django/models.py` | Already deprecated alias |
| `VersionTree` | `VersionTree` | `locator.py` | Deprecated; `DeprecationWarning` in `__init__` |
| `BundleDefinitionLocator` | `BundleDefinitionLocator` | `locator.py` | Already deprecated |
| `SlashSeparatedCourseKey` | `SlashSeparatedCourseKey` | `locations.py` | Already deprecated |
| `LocationBase` | `LocationBase` | `locations.py` | Already deprecated |
| `Location` | `Location` | `locations.py` | Already deprecated |
| `DeprecatedLocation` | `DeprecatedLocation` | `locations.py` | Already deprecated |
| `AssetLocation` | `AssetLocation` | `locations.py` | Already deprecated |

---

## Part 2: Code Field Renames

Fields that are slug-like codes but lack `_code` suffix. Changes cascade from abstract
bases down to concrete classes; old names get deprecated `@property` aliases and old
kwarg names get compat handling in `__init__`.

### `impl/contexts.py`

| Class | Old field | New field | Notes |
|---|---|---|---|
| `CourselikeKey` | `org` | `org_code` | abstract property |
| `CourselikeKey` | `course` | `course_code` | abstract property |
| `CourselikeKey` | `run` | `run_code` | abstract property |
| `CourseRunKey` | `org` | `org_code` | KEY_FIELDS + kwarg |
| `CourseRunKey` | `course` | `course_code` | KEY_FIELDS + kwarg |
| `CourseRunKey` | `run` | `run_code` | KEY_FIELDS + kwarg |
| `CourseRunKey` | `branch` | `branch_code` | KEY_FIELDS + kwarg |
| `LegacyLibraryKey` | `org` | `org_code` | KEY_FIELDS + kwarg |
| `LegacyLibraryKey` | `library` | `library_code` | KEY_FIELDS + kwarg |
| `LegacyLibraryKey` | `branch` | `branch_code` | KEY_FIELDS + kwarg |
| `LibraryKey` | `org` | `org_code` | KEY_FIELDS + kwarg |
| `LibraryKey` | `slug` | `library_code` | KEY_FIELDS + kwarg; slug IS the library code |

### `impl/usages.py`

| Class | Old field | New field | Notes |
|---|---|---|---|
| `UsageKey` | `block_type` | `type_code` | abstract property |
| `UsageKey` | `block_id` | `block_code` | abstract property |
| `CourseRunUsageKey` | `block_type` | `type_code` | KEY_FIELDS + kwarg; inherited by `LegacyLibraryUsageKey` |
| `CourseRunUsageKey` | `block_id` | `block_code` | KEY_FIELDS + kwarg; inherited similarly |
| `LibraryUsageKey` | `block_type` | `type_code` | KEY_FIELDS + kwarg |
| `LibraryUsageKey` | `usage_id` | `usage_code` | KEY_FIELDS + kwarg |
| `AsideUsageKey` | `aside_type` | `aside_type_code` | abstract property; can't be `type_code` — class also inherits `type_code` from `UsageKey` |
| `AsideUsageKeyV1/V2` | `aside_type` | `aside_type_code` | KEY_FIELDS + kwarg |

### `impl/assets.py`

| Class | Old field | New field | Notes |
|---|---|---|---|
| `AssetKey` | `asset_type` | `type_code` | abstract property |

`AssetKey.path` — leave as `path` (file path, not a code).
`CourseRunAssetKey.asset_type` (old alias for `type_code`) — deprecated property.
`CourseRunAssetKey.path` (alias for `block_code`) — kept without deprecation warning.

### `impl/collections.py`

| Class | Old field | New field | Notes |
|---|---|---|---|
| `CollectionKey` | `collection_id` | `collection_code` | KEY_FIELDS + kwarg |

### `impl/containers.py`

| Class | Old field | New field | Notes |
|---|---|---|---|
| `LibraryContainerKey` | `container_type` | `container_type_code` | KEY_FIELDS + kwarg |
| `LibraryContainerKey` | `container_id` | `container_code` | KEY_FIELDS + kwarg |

### `impl/definitions.py`

| Class | Old field | New field | Notes |
|---|---|---|---|
| `DefinitionKey` | `block_type` | `type_code` | abstract property |
| `CourseRunDefinitionKey` | `block_type` | `type_code` | KEY_FIELDS + kwarg |
| `AsideDefinitionKey` | `aside_type` | `aside_type_code` | abstract property; can't be `type_code` — class also inherits `type_code` from `DefinitionKey` |
| `AsideDefinitionKeyV1/V2` | `aside_type` | `aside_type_code` | KEY_FIELDS + kwarg |

`CourseRunDefinitionKey.definition_id` — leave as-is; it's a BSON `ObjectId`.

---

## Part 3: Implementation Order

1. **`openedx_keys/` scaffold** — create package, `impl/` dirs, empty `api.py`, empty `legacy_api.py`
2. **`impl/base.py`** — port `CourseObjectMixin`, `i4xEncoder`, `LocalId`, `CheckFieldMixin`; re-export exceptions; define `__all__`
3. **`impl/contexts.py`** — port and rename context hierarchy; rename abstract properties; deprecated kwarg compat; define `__all__`
4. **`impl/usages.py`** — port and rename usage hierarchy; merge `Locator`/`BlockLocatorBase` → `CourselikeUsageKey`; port aside usage keys; define `__all__`
5. **`impl/assets.py`** — port and rename asset hierarchy; define `__all__`
6. **`impl/collections.py`** — port concrete `CollectionKey`; absorb abstract; define `__all__`
7. **`impl/containers.py`** — port and rename container hierarchy; define `__all__`
8. **`impl/definitions.py`** — port and rename definition hierarchy; port aside definition keys; define `__all__`
9. **`impl/fields.py`** — port and rename Django field classes (excluding `BlockTypeKeyField`); define `__all__`
10. **`api.py`** — wire up wildcard imports from all `impl/` modules
11. **`legacy_api.py`** — port `BlockTypeKey`, `BlockTypeKeyV1`, `BlockTypeKeyField`, `LocationKeyField`, `VersionTree` (with `DeprecationWarning`), `BundleDefinitionLocator`, and all `locations.py` classes
12. **`openedx_keys/` setup** — add to `setup.py` `find_packages()`, entry points pointing to new class names; add `openedx_keys` to tox.ini and all linting/test tooling
13. **Compat `opaque_keys/edx/keys.py`** — module-level `__getattr__` re-exporting from `openedx_keys.api` with old names + deprecation warnings
14. **Compat `opaque_keys/edx/locator.py`** — same pattern; `VersionTree` shim → `openedx_keys.legacy_api`
15. **Compat `opaque_keys/edx/asides.py`** — same pattern
16. **Compat `opaque_keys/edx/block_types.py`** — shim → `openedx_keys.legacy_api`
17. **Compat `opaque_keys/edx/django/models.py`** — shim → `openedx_keys.api` (most fields) and `openedx_keys.legacy_api` (`BlockTypeKeyField`, `LocationKeyField`)
18. **Compat `opaque_keys/edx/locations.py`** — shim → `openedx_keys.legacy_api`; `i4xEncoder` shim → `openedx_keys.api.i4xEncoder`
19. **`opaque_keys/` setup** — update `setup.py` entry points to new class names (via `openedx_keys`)
20. **Tests** — update to new names; add deprecation-warning assertion tests for old names via compat layer
