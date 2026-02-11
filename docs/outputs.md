# Outputs (artifacts)

Each run creates a timestamped folder under:

- `artifacts/<run_id>/`

Expected files include:

- `spec.md` (copied input)
- `spec_pack.json`
- `design_pack.json`
- `build_plan.json`
- `callbacks.log.jsonl` (one JSON line per dynamic task)
- `manifests/*.json` (dynamic task outputs)
- `generated_app/` (applied `FileManifest`s)
- `run_summary.json` (run metadata, task statuses, written files, warnings)

## Runnable output guarantee

Even if dynamic tasks produce imperfect manifests, the pipeline ensures a minimal runnable Python skeleton exists under:

- `artifacts/<run_id>/generated_app/`

Baseline files are created if missing (without overwriting):

- `pyproject.toml`
- `src/app/__init__.py`
- `src/app/__main__.py` (supports `python -m app --help` and `--demo`)
- `tests/test_smoke.py` (unittest; `python -m unittest`)

## Cost control (model pinning)

Agent models are pinned in:

- `src/multi_agent_engineering/config/agents.yaml`

Currently set to:

- `llm: gpt-4o-mini`
