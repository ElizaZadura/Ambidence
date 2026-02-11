# TODO (pick up later)

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
