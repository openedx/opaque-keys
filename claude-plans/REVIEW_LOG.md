# Review Log: openedx-keys refactoring (origin/master..HEAD)

Reviewer: Claude. Date: 2026-03-27.

The Review has been reviewed by Kyle, who has indicated his preferred course of
action, indicated below by "Kyle:".

---

## Findings

### F1 [Medium] `BackcompatInitMixin` conflict check deviates from plan

**File:** `openedx_keys/impl/base.py:118`

The plan says: `if new in kwargs: raise TypeError(...)`. The implementation adds
`and kwargs[new] is not None`, meaning `CourseRunKey(org='mit', org_code=None)`
would silently accept the deprecated kwarg and overwrite `org_code=None` with
`org='mit'` instead of raising a `TypeError`. Callers explicitly passing
`org_code=None` alongside `org='something'` won't be told they're doing something
wrong.

In practice, this code path may be dead for the three concrete context classes
(which do their own inline translation), but future classes relying solely on
the mixin would be affected.

Kyle: The behavior is acceptable. No change needed.

---

### F2 [Low] `BackcompatInitMixin` is dead code for CourseRunKey, LegacyLibraryKey, LibraryKey

**Files:**
- `openedx_keys/impl/contexts.py:230-248` (CourseRunKey.__init__)
- `openedx_keys/impl/contexts.py:575-589` (LegacyLibraryKey.__init__)
- `openedx_keys/impl/contexts.py:865-879` (LibraryKey.__init__)

All three concrete classes handle deprecated kwarg translation manually in their
`__init__` before calling `super().__init__()`. By the time `BackcompatInitMixin.__init__`
runs, old kwargs are already consumed. This makes `BackcompatInitMixin` + `RENAMED_KWARGS`
on these classes misleading/dead code. Consider documenting this or removing the
mixin from classes that do their own translation.

Kyle: Good observation. This makes me want to do a refactoring. I think BackcompatInitMixin is
too magical and also too brittle--notice how it would be hard to refactor the `__init__`s in
contexts.py in order to use BackcompatInitMixin, so we end up with dupliated code. Here's what
I'd like to do instead: Every `__init__` should just accept `kwargs` for any argument TODO

    org_code, library_code = translate_backcompat_kwargs(kwargs, ("library", ))

---

### F3 [Low] `stacklevel=2` in `BackcompatInitMixin` would point to wrong frame

**File:** `openedx_keys/impl/base.py:125`

When called via `super().__init__()` from a subclass, the call stack is deeper
than 2 frames from the caller's code. The warning would point to the
`super().__init__()` line inside the subclass, not the original caller. Low
severity since inline code handles it for current classes.

---

### F4 [Medium] `LegacyLibraryKey.course_code` and `run_code` warn on the NEW canonical name

**File:** `openedx_keys/impl/contexts.py:686-703`

`LegacyLibraryKey` implements the abstract `course_code` and `run_code` properties
(the NEW canonical names from `CourselikeKey`) but they emit `DeprecationWarning`.
This means code that migrates from `key.course` to `key.course_code` (following
the deprecation guidance) will *still* get warnings if the key is a `LegacyLibraryKey`.

The original had no warning for accessing `course`/`run` through the base class
interface; warnings only fired for deprecated alias names. This is a new
backwards-incompatibility: downstream code doing the right thing gets warned.

Consider making these warning-free, or documenting this as intentional.

---

### F5 [Medium] `LegacyLibraryUsageKey.replace()` missing `name`/`category` kwarg compat

**File:** `openedx_keys/impl/usages.py:601-622`

In the original, `LibraryUsageLocator.replace()` called `super().replace(**kwargs)`
which went to `BlockUsageLocator.replace()`, which mapped `name`->`block_id` and
`category`->`block_type`. In the new code, `LegacyLibraryUsageKey.replace()` calls
`super(CourseRunUsageKey, self).replace(**kwargs)` (skipping `CourseRunUsageKey.replace()`).
It handles `block_id`->`block_code` and `block_type`->`type_code`, but does NOT handle
`name`->`block_code` or `category`->`type_code`.

Any caller doing `legacy_lib_usage_key.replace(name='foo')` or `replace(category='bar')`
would get an unexpected kwarg error.

**Fix:** Add `name`->`block_code` and `category`->`type_code` translations.

---

### F6 [Medium] `AsideUsageKeyV1/V2` constructors don't accept `aside_type` kwarg

**File:** `openedx_keys/impl/usages.py:923, 1020`

The parameter was renamed from `aside_type` to `aside_type_code` in the `__init__`
signature. There is no `BackcompatInitMixin` in the MRO, no `**kwargs` to catch
the old name, and no `RENAMED_KWARGS` mapping. Downstream code calling
`AsideUsageKeyV2(key, aside_type='foo')` with keyword argument would get `TypeError`.

Positional callers and `_from_string` use positional args, so they're fine.
Risk depends on how common kwarg usage is downstream.

**Fix:** Add `BackcompatInitMixin` with `RENAMED_KWARGS = {'aside_type': 'aside_type_code'}`,
or add manual translation.

---

### F7 [Low] `CourseRunUsageKey.__init__` adds new `isinstance` check on `course_key`

**File:** `openedx_keys/impl/usages.py:197-200`

The original `BlockUsageLocator.__init__` had no explicit type check on `course_key`.
The new code raises `TypeError` if not a `CourselikeKey`. Reasonable validation but
technically a new restriction that could break code passing a non-conforming object.

---

### F8 [High] `legacy_api.i4xEncoder` is non-functional as a JSON encoder

**File:** `openedx_keys/legacy_api.py:340-352`

The class creates `self._real` but never uses it. In the original `locations.py`,
`i4xEncoder` subclassed the real `i4xEncoder` from `keys.py` and called
`super().__init__()`. The new version subclasses `object` (implicitly), not
`json.JSONEncoder`. The `default()` method is never defined. Any call like
`json.dumps(obj, cls=legacy_i4xEncoder)` will fail because `object` is not a
valid JSON encoder class.

**Fix:** Subclass `json.JSONEncoder` (or the real `i4xEncoder` from
`openedx_keys.api`), and delegate `default()` properly.

---

### F9 [Medium] `DeprecatedLocation._to_string` emits spurious deprecation warnings

**File:** `openedx_keys/legacy_api.py:537`

`self.org`, `self.course`, `self.run` are now `@property` methods on
`CourseRunUsageKey` that emit `DeprecationWarning`. The original `locations.py`
used these as real field names (no warnings). Now every `str()` on a
`DeprecatedLocation` emits 3 deprecation warnings.

Same issue in `Location.replace` (lines 494-498) and `AssetLocation.replace`
(lines 550-555).

**Fix:** Use `self.course_key.org_code`, `.course_code`, `.run_code` instead
of `self.org`, `.course`, `.run`.

---

### F10 [Low] No compat shim tests for `opaque_keys.edx.django.models`

**File:** `tests/test_compat_shims.py` (gap)

The test file covers shims for `locator.py`, `keys.py`, `asides.py`,
`block_types.py`, and `locations.py`, but has zero tests for the
`opaque_keys.edx.django.models` compat shim. No verification that
`LearningContextKeyField` emits deprecation and resolves to `ContextKeyField`,
or that other field re-exports work.

---

### F11 [Medium] No tests for field-level rename deprecation warnings or RENAMED_KWARGS

**File:** `tests/test_compat_shims.py` (gap)

No tests that `course_run_key.org` emits `DeprecationWarning`, that
`usage_key.block_type` emits `DeprecationWarning`, that
`CourseRunKey(org='MIT', course='6.002x', run='2014')` works with warnings, etc.
The compat shim tests only cover class-level renames (import paths), not
field-level renames or kwarg compat. This is a significant coverage gap.

---

### F12 [Low] `opaque_keys/edx/locator.py` shim raises `AttributeError`, not `ImportError`

**File:** `opaque_keys/edx/locator.py:56`

The plan specifies "Unknown names raise `ImportError`" but the locator shim
raises `AttributeError`. Python's import machinery converts this to `ImportError`
for `from X import Y`, so `from` imports work, but `getattr(module, name)`
gets `AttributeError` instead of `ImportError`. Inconsistent with the plan
and with other shim modules.

---

### F13 [High] `CourseRunDefinitionKey` missing deprecated `block_type` kwarg handling

**File:** `openedx_keys/impl/definitions.py:74-91`

`CourseRunDefinitionKey.__init__` takes `type_code` as its first positional
parameter but has no handling for the old `block_type` keyword argument. The
original `DefinitionLocator.__init__` signature was
`(block_type, definition_id, deprecated=False)`.

Downstream code calling `CourseRunDefinitionKey(block_type='problem', definition_id=some_id)`
would pass `block_type` through to `**kwargs`, which reaches `OpaqueKey._unchecked_init`
and gets silently `setattr`'d as a spurious attribute while `type_code` stays `None`.

The class lacks both `RENAMED_KWARGS` and `BackcompatInitMixin`.

**Fix:** Add `BackcompatInitMixin` with `RENAMED_KWARGS = {'block_type': 'type_code'}`,
or add manual kwarg translation in `__init__`.

---

### F14 [High] `AsideDefinitionKeyV1/V2` missing deprecated `aside_type` kwarg handling

**File:** `openedx_keys/impl/definitions.py:189, 253`

Both `AsideDefinitionKeyV2.__init__(self, definition_key, aside_type_code, ...)`
and `AsideDefinitionKeyV1.__init__` have no handling for the old `aside_type`
keyword argument. The original signature was `(definition_key, aside_type, ...)`.

Keyword-arg callers like `AsideDefinitionKeyV2(def_key, aside_type='my_aside')`
would get `TypeError`. Positional callers still work fine.

Same class of bug as F6 (AsideUsageKeyV1/V2).

---

### F15 [High] `opaque_keys/edx/django/models.py` shim raises `AttributeError`, not `ImportError`

**File:** `opaque_keys/edx/django/models.py:34`

Same issue as F12 but in the Django models shim. `__getattr__` for unknown names
raises `AttributeError` instead of `ImportError`. Downstream code using
`try: from opaque_keys.edx.django.models import Foo except ImportError: ...`
would not catch the error and would crash.

---

### F16 [High] `opaque_keys/edx/keys.py` missing `OpaqueKey` re-export

**File:** `opaque_keys/edx/keys.py`

The original `keys.py` had `from opaque_keys import OpaqueKey` at module level,
making `from opaque_keys.edx.keys import OpaqueKey` work. The compat shim does
not re-export `OpaqueKey`. Any downstream code doing
`from opaque_keys.edx.keys import OpaqueKey` will fail with `ImportError`.

The plan's own example explicitly lists `OpaqueKey` as a re-export.

---

### F17 [High] `setup.py` test entry points reference deleted module

**File:** `setup.py:155-157`

The `opaque_keys.testing` entry points still reference
`opaque_keys.tests.test_opaque_keys:Base10Key` etc., but `opaque_keys/tests/`
was deleted in Step 20. The test key classes now live in `test_utils/test_keys.py`.

```python
'opaque_keys.testing': [
    'base10 = opaque_keys.tests.test_opaque_keys:Base10Key',  # BROKEN
    'hex = opaque_keys.tests.test_opaque_keys:HexKey',        # BROKEN
    'dict = opaque_keys.tests.test_opaque_keys:DictKey',      # BROKEN
],
```

This will cause stevedore to fail when loading test entry points.

---

---

## Summary

### High severity (likely to break downstream)

| # | Finding | File |
|---|---------|------|
| F8 | `legacy_api.i4xEncoder` not a JSONEncoder subclass — `json.dumps(cls=...)` breaks | `legacy_api.py:340` |
| F13 | `CourseRunDefinitionKey` missing `block_type` kwarg compat — silently sets spurious attr | `impl/definitions.py:74` |
| F14 | `AsideDefinitionKeyV1/V2` missing `aside_type` kwarg compat — TypeError for kwarg callers | `impl/definitions.py:189,253` |
| F16 | `keys.py` shim missing `OpaqueKey` re-export — import fails | `opaque_keys/edx/keys.py` |
| F17 | `setup.py` test entry points reference deleted `opaque_keys/tests/` module | `setup.py:155-157` |

### Medium severity (new warnings, missing compat, test gaps)

| # | Finding | File |
|---|---------|------|
| F1 | `BackcompatInitMixin` conflict check allows silent override when new kwarg is None | `impl/base.py:118` |
| F4 | `LegacyLibraryKey.course_code`/`run_code` warn on the NEW canonical name | `impl/contexts.py:686` |
| F5 | `LegacyLibraryUsageKey.replace()` missing `name`/`category` kwarg compat | `impl/usages.py:601` |
| F6 | `AsideUsageKeyV1/V2` constructors don't accept `aside_type` kwarg | `impl/usages.py:923,1020` |
| F9 | `DeprecatedLocation._to_string` emits 3 spurious deprecation warnings per call | `legacy_api.py:537` |
| F11 | No tests for field-level rename deprecation warnings or RENAMED_KWARGS | `test_compat_shims.py` |
| F15 | `django/models.py` shim raises `AttributeError` not `ImportError` | `django/models.py:34` |

### Low severity (minor inconsistencies, pre-existing gaps)

| # | Finding | File |
|---|---------|------|
| F2 | `BackcompatInitMixin` dead code for 3 context classes | `impl/contexts.py` |
| F3 | `stacklevel=2` in mixin would point to wrong frame | `impl/base.py:125` |
| F7 | New `isinstance` check on `course_key` in `CourseRunUsageKey.__init__` | `impl/usages.py:197` |
| F10 | No compat shim tests for `django.models` | `test_compat_shims.py` |
| F12 | `locator.py` shim raises `AttributeError` not `ImportError` | `locator.py:56` |

