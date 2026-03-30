# openedx-keys

## Meta
- This file is maintained as a living document during our refactoring work.
- Updated continuously so a fresh context can resume from where we left off.

## Environment and tooling
- Python: 3.12 via uv venv at `.venv`
- Always use `--python /Users/kyle/openedx/openedx-keys/.venv/bin/python` with `uv pip` (env var expansion doesn't work in settings.local.json PATH)
- For `python`/`pytest`/etc., use absolute path: `/Users/kyle/openedx/openedx-keys/.venv/bin/python`
- Ensure test requirements are installed: `-e .[django]` and `-r requirements/test.txt`,
- No global settings editing — only `.claude/settings.local.json` in this dir
- Don't use `tox` or `make` for QA. Here are the tools for testing and analysis,
  which should all be available in the python environment:
  - `pytest`
  - `pylint`
  - `pycodestyle`
  - `mypy`
- Dirs to lint and typecheck: `opaque_keys`, `openedx_keys`
- Dirs to test: `tests`
- Don't edit linting or pep configs. Ask user before suppressing new warnings.
- Fine to ignore IDE diagnostics unless they are actively helful
  to achieve the task.

## Repos
- `opaque-keys/` — clone of https://github.com/openedx/opaque-keys (edx-opaque-keys, installed as `-e .`)
  - Dev deps: `requirements/dev.txt` (not `development.txt`)
- `openedx-proposals/` — clone of https://github.com/openedx/openedx-proposals, branch `kdmccormick/keys`

## Project Overview
opaque-keys is an Open edX library that defines an abstraction layer for "opaque" key/identifier types (course keys, usage keys, etc.) with pluggable backends via stevedore.

## Background: OEP-0068 (Learning Content Identifiers)
Source: `openedx-proposals/oeps/best-practices/oep-0068-bp-content-identifiers.rst` (branch `kdmccormick/keys`)
Author: Kyle McCormick. Status: Draft.

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

## Refactoring Plan

We have iterated on a refactoring plan, and saved each successive version
to `./PLAN_$N.md`. Each PLAN document should be a self-contained point-in-time record.

The latest plan is the PLAN document with the greatest `$N`. Please read it now.
Confirm to the user you've read it, tell the user if you understand it, and if
you are confused, don't hesitate to ask the user for clarification.

Whenever we come to new decisions, write the new version out to
`PLAN_V<N+1>.md`. Ensure it's self-contained, so that a reader won't need to
read the old plan documents *unless* they want to understand the history. Don't
update old plan documents.

When you're refactoring, it's OK to pause an ask questions. Whenever there's a new
decision or direction or significant insight to record, consider it a new plan version.

When CLAUDE.md and a PLAN conflict, listen to CLAUDE.md, but also surface the
dissonance to the user.

## Current Status
- [x] Venv created (Python 3.12)
- [x] opaque-keys cloned and deps installed
- [x] openedx-proposals cloned, OEP-0068 read
- [x] Codebase scanned, refactoring plan drafted and iterated (v1–v9)
- [x] `openedx_keys/` impl modules complete
- [x] All compat shims complete (keys.py, locator.py, asides.py, block_types.py, django/models.py, locations.py)
- [x] Entry points in setup.py updated to new `openedx_keys.impl.*` class names
- [x] 394/394 non-Django tests pass
- [x] Step 20 complete: tests reorganized to flat `tests/` layout, `test_utils/` helper package created
- [x] Step 21 complete: `tests/test_compat_shims.py` created (422/422 tests pass)
- [x] Step 22 complete: `tests/test_fields.py` created (422 passed + 1 skipped without Django)
- [ ] All PLAN_V9 steps complete — consider next steps (linting, changelog, final review)

## Notes
- Multiple repos may be cloned as siblings under this directory.
- `definition_id` in `DefinitionLocator` is a BSON `ObjectId` — not a code/UUID/PK; leave as-is.
- Deprecation warning pattern already used throughout codebase: `warnings.warn(..., DeprecationWarning, stacklevel=2)`
- Entry points in setup.py use class import paths — update to new names to avoid spurious dep warnings on stevedore load.
