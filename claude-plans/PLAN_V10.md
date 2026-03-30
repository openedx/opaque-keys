# V10 Plan

This document is **self-contained** — it supersedes all prior PLAN_V* files.
It reflects the state of the project as of the completion of the V9 work session.

---

## Background: OEP-0068 (Learning Content Identifiers)

Source: `openedx-proposals/oeps/best-practices/oep-0068-bp-content-identifiers.rst`
(branch `kdmccormick/keys`). Author: Kyle McCormick. Status: Draft.

Open edX has four identifier categories:

| Category | Python type | Naming convention |
|---|---|---|
| Integer Primary Key | `int` | `id`/`_id` on models; `_pk` everywhere else |
| Code | `str` | `_code` |
| OpaqueKey | subclass of `OpaqueKey` | `_key` (object), `_key_string` (raw string) |
| UUID | `uuid.UUID` | `_uuid` (object), `_uuid_string` (raw string) |

**Old patterns to stop using:**
- `_id` for OpaqueKeys (e.g. `course_id`) — use `_key`
- `_id` or `_key` for codes — use `_code`
- `*Locator` class names → rename to `*Key`

---

## Part 0: Tooling & Development Workflow

### Environment Setup

```bash
uv venv --python 3.12 .venv
uv pip install --python /Users/kyle/openedx/openedx-keys/.venv/bin/python \
    -e opaque-keys -r opaque-keys/requirements/dev.txt
```

Always invoke Python/pytest via absolute venv path:
```bash
/Users/kyle/openedx/openedx-keys/.venv/bin/python
/Users/kyle/openedx/openedx-keys/.venv/bin/pytest
```

### Validation Commands

Run from `opaque-keys/` (where `setup.cfg`, `.pep8`, `pylintrc`, etc. live):

```bash
# Style — covers both packages
pycodestyle --config=.pep8 opaque_keys openedx_keys

# Type checking
mypy  # picks up mypy.ini / setup.cfg config

# Linting — covers both packages
pylint --rcfile=pylintrc opaque_keys openedx_keys

# Tests
pytest -v --disable-pytest-warnings --nomigrations
```

`testpaths = tests` is set in `setup.cfg` so pytest picks up `tests/` automatically.

### Git Commit Strategy

All work is committed to the `opaque-keys/` git repository. Commit frequently —
after each numbered step at minimum. Intermediate commits are allowed to fail tests;
the suite should be green by the end of each major part.

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
                            #   LocalId, CheckFieldMixin, i4xEncoder,
                            #   BackcompatInitMixin
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

tests/                      # flat test directory (see Part 4)
test_utils/                 # shared test helpers (importable, not collected by pytest)
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
from openedx_keys.impl.base import *  # noqa: F401, F403
from openedx_keys.impl.contexts import *  # noqa: F401, F403
from openedx_keys.impl.usages import *  # noqa: F401, F403
from openedx_keys.impl.assets import *  # noqa: F401, F403
from openedx_keys.impl.collections import *  # noqa: F401, F403
from openedx_keys.impl.containers import *  # noqa: F401, F403
from openedx_keys.impl.definitions import *  # noqa: F401, F403
from openedx_keys.impl.fields import *  # noqa: F401, F403
```

Each `impl/` module defines `__all__` listing only its public symbols.

---

## Critical Implementation Notes

### Stevedore entry-point sequencing

`OpaqueKey._drivers()` builds an `EnabledExtensionManager` with:

```python
EnabledExtensionManager(
    cls.KEY_TYPE,  # e.g. 'context_key'
    check_func=lambda extension: issubclass(extension.plugin, cls),
    invoke_on_load=False,
)
```

The `check_func` means stevedore **silently discards** any registered plugin whose
class is not a subclass of `cls`. Consequence:

- If `setup.py` entry points point to `CourseRunKey` before the compat shims are in
  place, `CourseKey.from_string()` uses `check_func=issubclass(plugin, CourseKey)`.
  `CourseRunKey` does NOT inherit from `CourseKey`, so stevedore drops it → `KeyError`
  on lookup.
- **Fix**: Keep setup.py entry points pointing to the OLD classes until compat shims
  make `CourseKey` the same object as `CourselikeKey`. Only then switch entry points.

### Compat shims must cover abstract base classes

For stevedore to accept `CourseRunKey` as a valid `CourseKey` plugin, `CourseKey`
must be the same object as `CourselikeKey` at runtime. The compat shim for
`opaque_keys/edx/keys.py` must therefore **directly re-export** abstract bases:

```python
# opaque_keys/edx/keys.py  (compat shim — NOT just _ALIASES)
from openedx_keys.api import CourselikeKey as CourseKey      # re-export
from openedx_keys.api import ContextKey as LearningContextKey
# etc.
```

After this, `issubclass(CourseRunKey, CourseKey)` == `issubclass(CourseRunKey,
CourselikeKey)` == True, and stevedore's check passes.

The same logic applies to all other abstract bases:

| Old abstract | New abstract | Module |
|---|---|---|
| `LearningContextKey` | `ContextKey` | `opaque_keys.edx.keys` |
| `CourseKey` | `CourselikeKey` | `opaque_keys.edx.keys` |
| `UsageKey` | `UsageKey` | (unchanged; no shim needed) |
| `UsageKeyV2` | `ContentUsageKey` | `opaque_keys.edx.keys` |
| `Locator` | `CourselikeUsageKey` | `opaque_keys.edx.locator` |
| `BlockLocatorBase` | `CourselikeUsageKey` | `opaque_keys.edx.locator` |
| `AssetKey` | `AssetKey` | (unchanged) |
| `DefinitionKey` | `DefinitionKey` | (unchanged) |
| `CollectionKey` (abstract) | `CollectionKey` (concrete) | `opaque_keys.edx.keys` |
| `ContainerKey` | `ContainerKey` | (unchanged) |
| `BlockTypeKey` | `BlockTypeKey` | (unchanged) |

### LOADED_DRIVERS cache

`OpaqueKey.LOADED_DRIVERS` is a class-level dict that caches driver managers. If
any code triggers `_drivers()` before the compat shims are in place, the broken
(empty) driver set will be cached. To be safe, clear the cache after installing
compat shims if any imports happened before:

```python
OpaqueKey.LOADED_DRIVERS.clear()  # in tests or setup if needed
```

In practice this is not required if compat shims are in place before any `from_string`
call. The test suite starts fresh each run so caching is not an issue there.

---

## Backwards Compatibility Mechanisms

**Class renames:** New class lives in `openedx_keys/impl/`. Compat module exposes old
name via module-level `__getattr__` → `DeprecationWarning`. Old name is the same class
object so `isinstance` checks work unchanged.

**Field/property renames:** Primary storage uses new `_code` name. Old name exposed as
a `@property` that emits `DeprecationWarning` and delegates to new name.

**Constructor kwarg renames:** Handled automatically by `BackcompatInitMixin` (see
below). Subclasses only declare `RENAMED_KWARGS`. Error if both old and new supplied.

**Django field renames:** Same module-level `__getattr__` pattern in compat
`django/models.py`. `KEY_CLASS` on each field points to the new key class.

**Entry points in setup.py:** Reference new class names directly once compat shims
are live (avoids spurious deprecation warnings on stevedore load).

### Compat module pattern — full detail

Shim modules use module-level `__getattr__` to intercept attribute access for renamed
symbols. **Unknown names raise `ImportError`**, not `AttributeError` — this matches
the error Python itself raises for a failed `from module import name`.

Abstract base classes that are merely renamed are **directly re-exported at module
level** (not via `__getattr__`) so that `isinstance`/`issubclass` checks work and
stevedore's `check_func` passes:

```python
# opaque_keys/edx/keys.py  (compat shim)
import warnings

# Direct re-exports of renamed abstract bases (same class object — issubclass works)
from openedx_keys.api import ContextKey as LearningContextKey        # noqa: F401
from openedx_keys.api import CourselikeKey as CourseKey              # noqa: F401
from openedx_keys.api import ContentUsageKey as UsageKeyV2           # noqa: F401
from openedx_keys.api import CollectionKey                           # noqa: F401  (absorbs old abstract)
# Unchanged abstracts — re-export as-is so imports from here still work
from openedx_keys.api import (                                        # noqa: F401
    UsageKey, AssetKey, DefinitionKey, ContainerKey,
    OpaqueKey, InvalidKeyError,
)

# Concrete/renamed classes accessed via __getattr__ (emits DeprecationWarning)
_ALIASES = {
    "CourseLocator": ...,
    ...
}

def __getattr__(name):
    if name in _ALIASES:
        warnings.warn(...)
        return _ALIASES[name]
    raise ImportError(f"cannot import name {name!r} from {__name__!r}")
```

### `BackcompatInitMixin` — centralised kwarg-rename machinery

Lives in `impl/base.py`. All new key classes that have renamed kwargs include it in
their MRO.

```python
class BackcompatInitMixin:
    RENAMED_KWARGS: dict[str, str] = {}

    def __init__(self, **kwargs):
        for old, new in self.RENAMED_KWARGS.items():
            if old in kwargs:
                if new in kwargs:
                    raise TypeError(f"Cannot supply both {old!r} (deprecated) and {new!r}")
                warnings.warn(f"Keyword argument {old!r} is deprecated; use {new!r} instead.",
                              DeprecationWarning, stacklevel=2)
                kwargs[new] = kwargs.pop(old)
        super().__init__(**kwargs)
```

Each subclass only declares the mapping — no bespoke `__init__` boilerplate:

```python
class CourseRunKey(BackcompatInitMixin, CourselikeKey):
    KEY_FIELDS = ("org_code", "course_code", "run_code", "branch", "version_guid")
    RENAMED_KWARGS = {
        "org": "org_code",
        "course": "course_code",
        "run": "run_code",
    }
    # No __init__ needed for kwarg compat — BackcompatInitMixin handles it.
```

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
| *(new)* | `BackcompatInitMixin` | New; centralises deprecated-kwarg translation |

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
kwarg names are listed in each class's `RENAMED_KWARGS`.

Note: `branch` is **not** renamed — it stays as `branch` on all key types that carry
it (legacy reasons; it does not follow the `_code` convention).

Note: `definition_id` in `DefinitionLocator`/`CourseRunDefinitionKey` is a BSON
`ObjectId` — not a code/UUID/PK; leave as-is.

### `impl/contexts.py`

| Class | Old field | New field | Notes |
|---|---|---|---|
| `CourselikeKey` | `org` | `org_code` | abstract property |
| `CourselikeKey` | `course` | `course_code` | abstract property |
| `CourselikeKey` | `run` | `run_code` | abstract property |
| `CourseRunKey` | `org` | `org_code` | KEY_FIELDS + RENAMED_KWARGS |
| `CourseRunKey` | `course` | `course_code` | KEY_FIELDS + RENAMED_KWARGS |
| `CourseRunKey` | `run` | `run_code` | KEY_FIELDS + RENAMED_KWARGS |
| `CourseRunKey` | `branch` | `branch` | **Unchanged** — legacy exception |
| `LegacyLibraryKey` | `org` | `org_code` | KEY_FIELDS + RENAMED_KWARGS |
| `LegacyLibraryKey` | `library` | `library_code` | KEY_FIELDS + RENAMED_KWARGS |
| `LegacyLibraryKey` | `branch` | `branch` | **Unchanged** — legacy exception |
| `LibraryKey` | `org` | `org_code` | KEY_FIELDS + RENAMED_KWARGS |
| `LibraryKey` | `slug` | `library_code` | KEY_FIELDS + RENAMED_KWARGS; slug IS the library code |

### `impl/usages.py`

| Class | Old field | New field | Notes |
|---|---|---|---|
| `UsageKey` | `block_type` | `type_code` | abstract property |
| `UsageKey` | `block_id` | `block_code` | abstract property |
| `CourseRunUsageKey` | `block_type` | `type_code` | KEY_FIELDS + RENAMED_KWARGS; inherited by `LegacyLibraryUsageKey` |
| `CourseRunUsageKey` | `block_id` | `block_code` | KEY_FIELDS + RENAMED_KWARGS; inherited similarly |
| `LibraryUsageKey` | `block_type` | `type_code` | KEY_FIELDS + RENAMED_KWARGS |
| `LibraryUsageKey` | `usage_id` | `usage_code` | KEY_FIELDS + RENAMED_KWARGS |
| `AsideUsageKey` | `aside_type` | `aside_type_code` | abstract property; can't be `type_code` — class also inherits `type_code` from `UsageKey` |
| `AsideUsageKeyV1/V2` | `aside_type` | `aside_type_code` | KEY_FIELDS + RENAMED_KWARGS |

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
| `CollectionKey` | `collection_id` | `collection_code` | KEY_FIELDS + RENAMED_KWARGS |

### `impl/containers.py`

| Class | Old field | New field | Notes |
|---|---|---|---|
| `LibraryContainerKey` | `container_type` | `container_type_code` | KEY_FIELDS + RENAMED_KWARGS |
| `LibraryContainerKey` | `container_id` | `container_code` | KEY_FIELDS + RENAMED_KWARGS |

### `impl/definitions.py`

| Class | Old field | New field | Notes |
|---|---|---|---|
| `DefinitionKey` | `block_type` | `type_code` | abstract property |
| `CourseRunDefinitionKey` | `block_type` | `type_code` | KEY_FIELDS + RENAMED_KWARGS |
| `AsideDefinitionKey` | `aside_type` | `aside_type_code` | abstract property; can't be `type_code` — class also inherits `type_code` from `DefinitionKey` |
| `AsideDefinitionKeyV1/V2` | `aside_type` | `aside_type_code` | KEY_FIELDS + RENAMED_KWARGS |

---

## Part 3: Implementation Steps

All steps are complete.

- [x] 1. **`openedx_keys/` scaffold** — package, `impl/` dir, empty `api.py`, `legacy_api.py`
- [x] 2. **`impl/base.py`** — `CourseObjectMixin`, `i4xEncoder`, `LocalId`, `CheckFieldMixin`, `BackcompatInitMixin`; re-export exceptions; define `__all__`
- [x] 3. **`impl/contexts.py`** — context hierarchy; renamed abstract properties; `RENAMED_KWARGS`; define `__all__`
- [x] 4. **`impl/usages.py`** — usage hierarchy; merge `Locator`/`BlockLocatorBase` → `CourselikeUsageKey`; aside usage keys; `RENAMED_KWARGS`; define `__all__`
- [x] 5. **`impl/assets.py`** — asset hierarchy; define `__all__`
- [x] 6. **`impl/collections.py`** — concrete `CollectionKey`; absorbs old abstract; define `__all__`
- [x] 7. **`impl/containers.py`** — container hierarchy; define `__all__`
- [x] 8. **`impl/definitions.py`** — definition hierarchy; aside definition keys; define `__all__`
- [x] 9. **`impl/fields.py`** — Django field classes (excluding `BlockTypeKeyField`); define `__all__`
- [x] 10. **`api.py`** — wildcard imports from all `impl/` modules
- [x] 11. **`legacy_api.py`** — `BlockTypeKey`, `BlockTypeKeyV1`, `BlockTypeKeyField`, `LocationKeyField`, `VersionTree` (with `DeprecationWarning`), `BundleDefinitionLocator`, all `locations.py` classes
- [x] 12a. **Revert setup.py entry points** to original old class names (was premature; done before compat shims)
- [x] 12b. **Config updates** — add `openedx_keys` to tox.ini quality commands (pycodestyle, pylint); update setup.cfg mypy config
- [x] 13. **Compat `opaque_keys/edx/keys.py`** — direct re-exports of abstract bases at module level; `__getattr__` for concrete/renamed classes; unknown names → `ImportError`
- [x] 14. **Compat `opaque_keys/edx/locator.py`** — same pattern; `VersionTree` shim → `openedx_keys.legacy_api`; re-export `CourselikeUsageKey` as both `Locator` and `BlockLocatorBase`
- [x] 15. **Compat `opaque_keys/edx/asides.py`** — same pattern
- [x] 16. **Compat `opaque_keys/edx/block_types.py`** — shim → `openedx_keys.legacy_api`
- [x] 17. **Compat `opaque_keys/edx/django/models.py`** — shim → `openedx_keys.api` (most fields) and `openedx_keys.legacy_api` (`BlockTypeKeyField`, `LocationKeyField`)
- [x] 18. **Compat `opaque_keys/edx/locations.py`** — shim → `openedx_keys.legacy_api`; `i4xEncoder` shim → `openedx_keys.api.i4xEncoder`
- [x] 19. **Update `setup.py` entry points** to new class names (via `openedx_keys` paths) — safe now because compat shims make old abstract base classes identical to new ones
- [x] 20. **Tests migration** — flat `tests/` layout; `test_utils/` helper package; `testpaths = tests` in setup.cfg
- [x] 21. **`tests/test_compat_shims.py`** — asserts `DeprecationWarning` for old names; `ImportError` for never-existed names; `isinstance`/`issubclass` checks pass (422/422 tests pass)
- [x] 22. **`tests/test_fields.py`** — Django model field tests (422 passed + 1 skipped without Django)

**Test results at end of step 22:** 422 passed, 1 skipped (Django field test skipped without Django settings).

---

## Part 4: Test Layout

### Pattern: `tests/` vs `test_utils/`

- `tests/` — flat directory of `test_*.py` files collected by pytest. No `__init__.py`.
- `test_utils/` — proper Python package (`__init__.py` present) for helpers/fixtures.
  pytest does not collect from here (no `test_*.py` files).

### Final test file layout

| Old location | New location | Notes |
|---|---|---|
| `opaque_keys/tests/strategies.py` | `test_utils/strategies.py` | Hypothesis strategies |
| `opaque_keys/tests/test_opaque_keys.py` | `tests/test_opaque_keys.py` | |
| `opaque_keys/edx/tests/test_aside_keys.py` | `tests/test_aside_keys.py` | |
| `opaque_keys/edx/tests/test_asset_locators.py` | `tests/test_asset_keys.py` | |
| `opaque_keys/edx/tests/test_block_types.py` | `tests/test_block_types.py` | |
| `opaque_keys/edx/tests/test_block_usage_locators.py` | `tests/test_usage_keys.py` | |
| `opaque_keys/edx/tests/test_collection_locators.py` | `tests/test_collection_keys.py` | |
| `opaque_keys/edx/tests/test_container_locators.py` | `tests/test_container_keys.py` | |
| `opaque_keys/edx/tests/test_course_locators.py` | `tests/test_course_keys.py` | |
| `opaque_keys/edx/tests/test_default_deprecated.py` | `tests/test_default_deprecated.py` | |
| `opaque_keys/edx/tests/test_deprecated_locations.py` | `tests/test_deprecated_locations.py` | |
| `opaque_keys/edx/tests/test_is_course.py` | `tests/test_is_context.py` | |
| `opaque_keys/edx/tests/test_library_locators.py` | `tests/test_library_keys.py` | |
| `opaque_keys/edx/tests/test_library_usage_locators.py` | `tests/test_library_usage_keys.py` | |
| `opaque_keys/edx/tests/test_locators.py` | `tests/test_locators_compat.py` | Legacy locator tests; keep until compat layer removed |
| `opaque_keys/edx/tests/test_properties.py` | `tests/test_properties.py` | |
| *(new)* | `tests/test_compat_shims.py` | `DeprecationWarning` and `ImportError` assertions |
| *(new)* | `tests/test_fields.py` | Django model field tests |

Old directories `opaque_keys/tests/` and `opaque_keys/edx/tests/` have been deleted.

`opaque_keys/edx/tests/__init__.py` previously exported `LocatorBaseTest` and
`TestDeprecated` — these were moved to `test_utils/` so they remain importable.

Django tests (`opaque_keys/edx/django/tests/`) stay where they are — they require
Django settings and run in a separate tox env.

---

## Current Status & Next Steps

**All implementation and test steps are complete.** The codebase is in a clean,
working state. Remaining work to close out the project:

- [ ] **Linting** — run `pycodestyle`, `pylint`, and `mypy` across `opaque_keys/` and
  `openedx_keys/`; fix any issues found
- [ ] **Changelog** — write a `CHANGELOG.rst` (or add an entry) documenting:
  - New `openedx_keys` package and `openedx_keys.api` / `openedx_keys.legacy_api`
  - All class renames (with old → new mapping)
  - All field renames (with old → new mapping and `DeprecationWarning` note)
  - The three intentional breaking changes (merged abstract classes)
  - Downstream migration guide
- [ ] **Final review** — read through `openedx_keys/` impl modules for any loose ends;
  verify all `__all__` lists are complete and accurate
