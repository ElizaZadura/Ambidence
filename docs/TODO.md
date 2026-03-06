# TODO (pick up later)

## Session 2026-03-06: Repo extraction fixes

Steps taken after extracting this project from the parent monorepo:

1. **Stripped stale `multi_agent_engineering.` import prefix** across 4 files
   (`main.py`, `crew.py`, `pipeline.py`, `manifest_applier.py`).
   The old package directory no longer exists; modules live flat under `src/`.

2. **Fixed `project_root_from_src_file`** in `artifact_store.py`.
   - Old: `parents[2]` (assumed `src/multi_agent_engineering/main.py` depth).
   - New: marker-based walk — searches upward for `pyproject.toml` or `.git`.
   - The `parents[N]` trick broke under hatchling editable installs where
     `__file__` resolves into `.venv/Lib/site-packages/`, not `src/`.
   - This was silently preventing `.env` from being found (API keys never loaded).

3. **Updated `pyproject.toml`** entry points and hatchling wheel config.
   - Entry points changed from `multi_agent_engineering.main:run` → `main:run` (etc).
   - Added explicit `packages` + `force-include` for the flat `src/` layout.
   - Added missing `__init__.py` to `src/models/` and `src/tools/`.
   - Reinstalled with `uv pip install -e .` to regenerate entry point scripts.

4. **Tightened `task_id` naming contract** to fix all-tasks-failing validation.
   - `plan_execution` prompt now requires `"task-1"`, `"task-2"`, `"task-3"` format.
   - Dynamic task description now explicitly states the required `task_id` value.
   - Validation demoted from hard `ValueError` to warn-and-normalize, so minor
     LLM naming drift doesn't kill an otherwise successful task.

**Worth noting:** The LLM still produced `task_1` (underscore) instead of `task-1`
(hyphen) in the first successful run. The safety-net normalization kept it moving.
If stricter enforcement is desired later, consider a Pydantic validator on
`PlannedTask.task_id` with a regex like `^task-\d+$`.

---

## Output shape / runnable skeleton

- [x] Ensure `generated_app/` output matches the intended Python layout:
  - [x] `pyproject.toml`
  - [x] `src/app/__init__.py`
  - [x] `src/app/__main__.py` (supports `python -m app --help` and `--demo`)
  - [x] `tests/test_smoke.py` (unittest; `python -m unittest`)
- [x] Add a minimal “smoke demo” path (`--demo`) that exercises domain + services + UI.

## Pipeline robustness

- [x] Log dynamic-task failures into `callbacks.log.jsonl` with `status=failed` and `blocking_issues`.
- [x] Make manifest application stricter/saner if needed:
  - [x] Decide whether to reject dotfiles / absolute paths / oversized files. (Yes: reject dotfiles; cap file size.)
  - [x] Decide whether `content_mode="fenced_code"` should warn vs. error when fences are missing. (Warn + fall back to literal.)

## Prompt hygiene

- [x] Keep `BuildPlan.owner_agent` constrained to the 4 agent IDs (avoid role strings / invented roles).
- [x] Keep dynamic tasks “Python-only” (no JS/TS) and docs minimal.

## Nice-to-haves

- [x] Add a short CLI flag for spec selection (`SPEC_FILE` is already supported).
- [x] Add a summary file per run (e.g. `run_summary.json`) listing written files and task statuses.
