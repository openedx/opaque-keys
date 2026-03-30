# V9 Plan

Snapshot of the V9 refactoring plan.
Key changes from V8:
- Updated implementation status: steps 1–19 are all complete (PLAN_V8 section
  "Current Implementation Status" is now fully done).
- 394/394 non-Django tests pass as of end of V8 work session.
- Only remaining step is step 20: test reorganization.

---

## Current Implementation Status (as of V9)

All implementation steps complete:

- [x] 1. `openedx_keys/` scaffold
- [x] 2. `impl/base.py`
- [x] 3. `impl/contexts.py`
- [x] 4. `impl/usages.py`
- [x] 5. `impl/assets.py`
- [x] 6. `impl/collections.py`
- [x] 7. `impl/containers.py`
- [x] 8. `impl/definitions.py`
- [x] 9. `impl/fields.py`
- [x] 10. `api.py` wired up
- [x] 11. `legacy_api.py` wired up
- [x] 12a. setup.py entry points already point to new `openedx_keys.impl.*` classes (no revert needed; compat shims make it valid)
- [x] 12b. tox/lint config updated (openedx_keys in quality commands)
- [x] 13. Compat `opaque_keys/edx/keys.py`
- [x] 14. Compat `opaque_keys/edx/locator.py`
- [x] 15. Compat `opaque_keys/edx/asides.py`
- [x] 16. Compat `opaque_keys/edx/block_types.py`
- [x] 17. Compat `opaque_keys/edx/django/models.py`
- [x] 18. Compat `opaque_keys/edx/locations.py`
- [x] 19. setup.py entry points use new class names (already done)
- [ ] 20. Tests migration (flat `tests/` layout)

---

## Remaining Work: Step 20 — Test Reorganization

### Pattern: `tests/` vs `test_utils/`

- `tests/` — flat directory of `test_*.py` files collected by pytest. No `__init__.py`.
- `test_utils/` — proper Python package (`__init__.py` present) for helpers/fixtures.
  pytest does not collect from here (no `test_*.py` files).

### Source mapping

| Old location | New location | Notes |
|---|---|---|
| `opaque_keys/tests/strategies.py` | `test_utils/strategies.py` | Hypothesis strategies; update imports |
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
| `opaque_keys/edx/tests/test_locators.py` | `tests/test_locators_compat.py` | |
| `opaque_keys/edx/tests/test_properties.py` | `tests/test_properties.py` | |
| *(new)* | `tests/test_compat_shims.py` | Asserts `DeprecationWarning` for old names; `ImportError` for never-existed names |
| *(new)* | `tests/test_fields.py` | Django model field tests (currently in django/tests/) |

### `conftest.py` and pytest config

Update `setup.cfg`:
```ini
[tool:pytest]
testpaths = tests
```

Add a top-level `conftest.py` (or move the existing one) if needed.

### Old `tests/` directories

Once the new `tests/` layout is confirmed green, delete:
- `opaque_keys/tests/`
- `opaque_keys/edx/tests/`

### `test_compat_shims.py` — new file

Tests that:
1. Importing old names from compat shims emits `DeprecationWarning`
2. `isinstance` / `issubclass` checks still work (e.g. `isinstance(key, CourseKey)`)
3. Importing a never-existed name raises `ImportError`

### Implementation notes

- `opaque_keys/edx/tests/__init__.py` currently exports `LocatorBaseTest` and
  `TestDeprecated` — these must move to `test_utils/` so they remain importable.
- The `conftest.py` at the repo root (or `opaque_keys/`) may need updating for
  `testpaths`.
- Django tests (`opaque_keys/edx/django/tests/`) stay where they are for now —
  they require Django settings and are in a separate tox env.
