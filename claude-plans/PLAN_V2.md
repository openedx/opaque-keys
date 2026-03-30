# V2 Plan (Archived)

Snapshot of the V2 refactoring plan from CLAUDE.md.
This is the "new package structure + compat layer" approach.

---

## New Package Structure

```
openedx_keys/               # new top-level dir, sibling to opaque-keys/
    __init__.py
    api.py                  # public facade: wildcard-imports all impl modules
    impl/
        __init__.py
        bases.py            # all abstract key types (from keys.py)
        keys.py             # all concrete key types (from locator.py)
        aside_keys.py       # aside key types (from asides.py)
        block_type_keys.py  # block type key types (from block_types.py)
        fields.py           # django model fields (from django/models.py)

opaque_keys/edx/            # becomes a compat mirror; each module re-exports
    keys.py                 # from openedx_keys.api, mapping new names → old names
    locator.py
    asides.py
    block_types.py
    django/
        models.py
    locations.py            # already deprecated; leave alone
```

Each `impl/` module defines `__all__` listing only its public classes. `api.py` does:
```python
from openedx_keys.impl.bases import *
from openedx_keys.impl.keys import *
# etc.
```

The compat modules import new names with underscore aliases (keeping them out of the
public namespace) and expose old names only via module-level `__getattr__`:
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

### `impl/bases.py` — Abstract classes (from `keys.py`)

| Old Name | New Name | Notes |
|---|---|---|
| `LearningContextKey` | `ContextKey` | |
| `CourseKey` | `CourselikeKey` | Very widely used downstream; compat alias critical |
| `UsageKeyV2` | `ContentUsageKey` | |
| `CollectionKey` | *(absorbed — see `impl/keys.py`)* | Abstract merged into the one concrete impl |
| `UsageKey` | `UsageKey` | Unchanged |
| `AssetKey` | `AssetKey` | Unchanged |
| `DefinitionKey` | `DefinitionKey` | Unchanged |
| `ContainerKey` | `ContainerKey` | Unchanged |
| `BlockTypeKey` | `BlockTypeKey` | Unchanged |

`CourselikeKey.make_usage_key(block_type, block_id)` signature → `make_usage_key(type_code, block_code)` (old kwarg names get compat handling).

### `impl/keys.py` — Concrete classes (from `locator.py`)

| Old Name | New Name | Notes |
|---|---|---|
| `CourseLocator` | `CourseRunKey` | nee `CourseLocator` |
| `LibraryLocator` | `LegacyLibraryKey` | nee `LibraryLocator` |
| `LibraryLocatorV2` | `LibraryKey` | nee `LibraryLocatorV2`; clean name, no version suffix |
| `Locator` | `CourselikeUsageKey` | Abstract; merged with `BlockLocatorBase` |
| `BlockLocatorBase` | `CourselikeUsageKey` | Abstract; merged with `Locator` |
| `BlockUsageLocator` | `CourseRunUsageKey` | nee `BlockUsageLocator` |
| `LibraryUsageLocator` | `LegacyLibraryUsageKey` | nee `LibraryUsageLocator` |
| `LibraryUsageLocatorV2` | `LibraryUsageKey` | nee `LibraryUsageLocatorV2`; clean name |
| `AssetLocator` | `CourseRunAssetKey` | nee `AssetLocator`; `AssetKey` stays separate |
| `LibraryCollectionLocator` | `CollectionKey` | Absorbs abstract `CollectionKey` from `keys.py` |
| `LibraryContainerLocator` | `LibraryContainerKey` | nee `LibraryContainerLocator` |
| `DefinitionLocator` | `CourseRunDefinitionKey` | nee `DefinitionLocator` |
| `BundleDefinitionLocator` | — | Already deprecated; leave alone |
| `LocalId` | `LocalId` | Utility class; moves to `impl/keys.py` unchanged |

`locations.py` deprecated classes — leave alone, stays in compat `opaque_keys/edx/locations.py`.

### `impl/fields.py` — Django model fields (from `django/models.py`)

| Old Name | New Name | Notes |
|---|---|---|
| `LearningContextKeyField` | `ContextKeyField` | `KEY_CLASS` → `ContextKey` |
| `CourseKeyField` | `CourseKeyField` | Unchanged name; `KEY_CLASS` → `CourselikeKey` |
| `UsageKeyField` | `UsageKeyField` | Unchanged |
| `ContainerKeyField` | `ContainerKeyField` | Unchanged |
| `CollectionKeyField` | `CollectionKeyField` | Unchanged name; `KEY_CLASS` → new `CollectionKey` |
| `BlockTypeKeyField` | `BlockTypeKeyField` | Unchanged |
| `LocationKeyField` | `LocationKeyField` | Already deprecated alias; leave alone |

---

## Part 2: Code Field Renames

### `impl/bases.py` — Abstract base classes

| Class | Old field | New field | Notes |
|---|---|---|---|
| `CourselikeKey` | `org` | `org_code` | abstract property |
| `CourselikeKey` | `course` | `course_code` | abstract property |
| `CourselikeKey` | `run` | `run_code` | abstract property |
| `DefinitionKey` | `block_type` | `type_code` | abstract property |
| `UsageKey` | `block_type` | `type_code` | abstract property |
| `UsageKey` | `block_id` | `block_code` | abstract property |
| `AssetKey` | `asset_type` | `type_code` | abstract property |
| `BlockTypeKey` | `block_type` | `type_code` | abstract property |
| `BlockTypeKey` | `block_family` | `family_code` | abstract property |
| `AsideDefinitionKey` | `aside_type` | `aside_type_code` | abstract property; can't be `type_code` — class also has `block_type` → `type_code` |
| `AsideUsageKey` | `aside_type` | `aside_type_code` | abstract property; same reason |

`AssetKey.path` — leave as `path` (file path, not a code).

### `impl/keys.py` — Concrete classes

| Class | Old field/kwarg | New field/kwarg | Notes |
|---|---|---|---|
| `CourseRunKey` | `org` | `org_code` | KEY_FIELDS + kwarg |
| `CourseRunKey` | `course` | `course_code` | KEY_FIELDS + kwarg |
| `CourseRunKey` | `run` | `run_code` | KEY_FIELDS + kwarg |
| `CourseRunKey` | `branch` | `branch_code` | KEY_FIELDS + kwarg |
| `LegacyLibraryKey` | `org` | `org_code` | KEY_FIELDS + kwarg |
| `LegacyLibraryKey` | `library` | `library_code` | KEY_FIELDS + kwarg |
| `LegacyLibraryKey` | `branch` | `branch_code` | KEY_FIELDS + kwarg |
| `LibraryKey` | `org` | `org_code` | KEY_FIELDS + kwarg |
| `LibraryKey` | `slug` | `library_code` | KEY_FIELDS + kwarg; slug IS the library code |
| `CourseRunUsageKey` | `block_type` | `type_code` | KEY_FIELDS + kwarg; inherited by `LegacyLibraryUsageKey`, `CourseRunAssetKey` |
| `CourseRunUsageKey` | `block_id` | `block_code` | KEY_FIELDS + kwarg; inherited similarly |
| `LibraryUsageKey` | `block_type` | `type_code` | KEY_FIELDS + kwarg |
| `LibraryUsageKey` | `usage_id` | `usage_code` | KEY_FIELDS + kwarg |
| `CollectionKey` | `collection_id` | `collection_code` | KEY_FIELDS + kwarg |
| `LibraryContainerKey` | `container_type` | `container_type_code` | KEY_FIELDS + kwarg |
| `LibraryContainerKey` | `container_id` | `container_code` | KEY_FIELDS + kwarg |
| `CourseRunDefinitionKey` | `block_type` | `type_code` | KEY_FIELDS + kwarg |

`CourseRunDefinitionKey.definition_id` — leave as-is; it's a BSON `ObjectId`.

`CourseRunAssetKey.asset_type` (alias for `type_code`) and `CourseRunAssetKey.path`
(alias for `block_code`) — keep `path` accessible without a deprecation warning (it's descriptive).

### `impl/block_type_keys.py`

| Class | Old field/kwarg | New field/kwarg |
|---|---|---|
| `BlockTypeKeyV1` | `block_type` | `type_code` |
| `BlockTypeKeyV1` | `block_family` | `family_code` |

### `impl/aside_keys.py`

| Class | Old field | New field | Notes |
|---|---|---|---|
| `AsideDefinitionKeyV1/V2` | `aside_type` | `aside_type_code` | Matches abstract rename in `bases.py` |
| `AsideUsageKeyV1/V2` | `aside_type` | `aside_type_code` | Same |

---

## Part 3: Implementation Order

1. **`openedx_keys/` scaffold** — create package, `impl/` dirs, empty `api.py`
2. **`impl/bases.py`** — port and rename abstract classes + abstract properties; define `__all__`
3. **`impl/block_type_keys.py`** — port and rename fields; deprecated properties + kwarg compat; define `__all__`
4. **`impl/aside_keys.py`** — port and rename `aside_type`; deprecated property + kwarg compat; define `__all__`
5. **`impl/keys.py`** — port and rename all concrete classes + fields; merge `Locator`/`BlockLocatorBase` → `CourselikeUsageKey`; merge abstract `CollectionKey` → `CollectionKey`; define `__all__`
6. **`impl/fields.py`** — port and rename field classes; define `__all__`
7. **`api.py`** — wire up wildcard imports from all impl modules
8. **`openedx_keys/` setup** — `pyproject.toml` / `setup.py`, entry points pointing to new class names
9. **Compat `opaque_keys/edx/keys.py`** — module-level `__getattr__` re-exporting from `openedx_keys.api` with old names + deprecation warnings
10. **Compat `opaque_keys/edx/locator.py`** — same pattern
11. **Compat `opaque_keys/edx/asides.py`**, **`block_types.py`**, **`django/models.py`** — same pattern
12. **`opaque_keys/` setup** — update `setup.py` entry points to new class names (via `openedx_keys`)
13. **Tests** — update to new names; add deprecation-warning assertion tests for old names via compat layer
