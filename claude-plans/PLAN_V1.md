# V1 Plan (Archived)

This was the original plan — in-place refactoring of the `opaque-keys` repo.
Superseded by the V2 plan in CLAUDE.md.

---

## Backwards Compatibility Mechanisms

**Class renames:** Define new class with new name; expose old name via module-level
`__getattr__` so importing the old name emits a `DeprecationWarning`. Old name remains
a true alias (same class object) so `isinstance` checks work unchanged.

**Field/property renames:** Primary storage uses new `_code` name. Old name exposed as
a `@property` that emits `DeprecationWarning` and delegates to new name.

**Constructor kwarg renames:** `__init__` accepts both old and new kwarg names. If old
name is used, emit `DeprecationWarning` and map to new name. Error if both supplied.

**Django field renames:** Same module-level `__getattr__` pattern for field class names.
`KEY_CLASS` on each field updated to point to the new key class.

**Entry points in setup.py:** Update to reference new class names directly (avoids
spurious deprecation warnings on stevedore load).

---

## Part 1: Class Renames

### Abstract / Intermediate Base Classes (`keys.py`)

| Old Name | New Name | Notes |
|---|---|---|
| `LearningContextKey` | `ContextKey` | |
| `CourseKey` | `CourselikeKey` | Very widely used downstream; compat alias critical |
| `UsageKeyV2` | `ContentUsageKey` | |
| `CollectionKey` | *(merged — see concrete classes)* | Abstract merged into the one concrete impl |
| `UsageKey` | `UsageKey` | Unchanged |
| `AssetKey` | `AssetKey` | Unchanged |
| `DefinitionKey` | `DefinitionKey` | Unchanged |
| `ContainerKey` | `ContainerKey` | Unchanged |
| `BlockTypeKey` | `BlockTypeKey` | Unchanged |

### Concrete Classes (`locator.py`)

| Old Name | New Name | Notes |
|---|---|---|
| `CourseLocator` | `CourseRunKey` | nee `CourseLocator` |
| `LibraryLocator` | `LegacyLibraryKey` | nee `LibraryLocator` |
| `LibraryLocatorV2` | `LibraryKey` | nee `LibraryLocatorV2`; clean name, no version suffix |
| `Locator` | `CourselikeUsageKey` | Merged with `BlockLocator` |
| `BlockLocatorBase` | `CourselikeUsageKey` | Merged with `Locator` |
| `BlockUsageLocator` | `CourseRunUsageKey` | nee `BlockUsageLocator` |
| `LibraryUsageLocator` | `LegacyLibraryUsageKey` | nee `LibraryUsageLocator` |
| `LibraryUsageLocatorV2` | `LibraryUsageKey` | nee `LibraryUsageLocatorV2`; clean name |
| `AssetLocator` | `CourseRunAssetKey` | nee `AssetLocator` |
| `LibraryCollectionLocator` | `CollectionKey` | Merges abstract `CollectionKey` + concrete `LibraryCollectionLocator` into one class |
| `LibraryContainerLocator` | `LibraryContainerKey` | nee `LibraryContainerLocator` |
| `DefinitionLocator` | `CourseRunDefinitionKey` | nee `DefinitionLocator` |
| `BundleDefinitionLocator` | — | Already deprecated; leave alone |

All `locations.py` deprecated classes — leave alone.

### Django Model Fields (`django/models.py`)

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

Fields that are slug-like codes but lack `_code` suffix. Changes cascade from abstract
bases down to concrete classes; old names get deprecated `@property` aliases and old
kwarg names get compat handling in `__init__`.

### `keys.py` — Abstract base classes

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

`AssetKey.path` — leave as `path` (file path, not a code).

### `locator.py` — Concrete classes

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

`CourseRunAssetKey.asset_type` (alias for `block_type` → `type_code`) and
`CourseRunAssetKey.path` (alias for `block_id` → `block_code`) — update aliases
accordingly; keep `path` accessible without a deprecation warning (it's descriptive).

### `block_types.py`

| Class | Old field/kwarg | New field/kwarg |
|---|---|---|
| `BlockTypeKeyV1` | `block_type` | `type_code` |
| `BlockTypeKeyV1` | `block_family` | `family_code` |

### `asides.py`

| Class | Old field | New field | Notes |
|---|---|---|---|
| `AsideDefinitionKeyV1/V2` | `aside_type` | `aside_type_code` | Can't be `type_code` — same class also exposes `block_type` → `type_code` |
| `AsideUsageKeyV1/V2` | `aside_type` | `aside_type_code` | Same reason |

---

## Part 3: Implementation Order

1. **`keys.py`** — rename abstract classes and abstract properties; add deprecated aliases
2. **`block_types.py`** — rename fields; add deprecated properties and kwarg compat
3. **`asides.py`** — rename `aside_type`; add deprecated property and kwarg compat
4. **`locator.py`** — rename all classes and fields; add deprecated class aliases
   (via module-level `__getattr__`) and deprecated field properties
5. **`django/models.py`** — rename field classes; add deprecated class aliases
6. **`setup.py`** — update entry_points to new class names
7. **Tests** — update to new names; add deprecation-warning assertion tests for old names
