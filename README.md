# MultiAgentEngineering (spec-driven, phase-gated crew)

This project is a **spec-driven engineering pipeline** built with [crewAI](https://crewai.com).

It runs a phase-gated workflow:

- `spec_intake` → `SpecPack`
- `design` → `DesignPack`
- `plan_execution` → `BuildPlan` (max 3 tasks)
- dynamic implementation tasks → `FileManifest`s → applied into an output folder

## Setup

- **Python**: >=3.10 <3.14
- **Dependencies**: this project is intended to be run via CrewAI’s project tooling

Put your API key in the project root `.env` (this repo loads it with override semantics to avoid stale keys winning):

- `OPENAI_API_KEY=...`

Install dependencies:

```bash
crewai install
```

## Running

### 1) Provide a spec file

This project expects a **separate spec file**. Easiest option:

- create `spec.md` in the project root (this repo already includes one you can edit)

Other options:

- set `SPEC_FILE=/path/to/spec.md` in your environment
- pass `--spec-file /path/to/spec.md` (or `--spec` / `-s`) when running

### 2) Run the crew

From this folder:

```bash
crewai run
```

## Outputs (artifacts)

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

## Troubleshooting

### 401 “invalid_api_key” but the key is valid

This usually means a **stale** `OPENAI_API_KEY` was already set in your shell and was not being overridden.
This project loads `.env` with override semantics; confirm your `.env` is correct in this folder and re-run.

### Manifest safety behavior

- Paths are applied under `generated_app/` and normalized (leading `generated_app/` is stripped if present).
- Dotfile paths are rejected.
- File size is capped (to avoid huge accidental outputs).
- If `content_mode="fenced_code"` is set but no fenced block is present, the pipeline writes the content literally and records a warning.

## Design notes

- Proposed changes discussion: `docs/proposed_changes_summary.txt`

## Summary of steps taken (high level)

- Added **Pydantic output schemas** for `DesignPack`, `BuildPlan`, and `FileManifest`.
- Updated **agent/task config** to match the phase-gated workflow and pinned models to `gpt-4o-mini`.
- Made the runner **spec-file driven** and added robust `.env` loading (override to avoid stale keys).
- Implemented an **artifacts pipeline** that writes `spec_pack.json`, `design_pack.json`, `build_plan.json`, plus callback logs.
- Added **dynamic task execution** from `BuildPlan` producing `FileManifest`s, and applied manifests into `artifacts/<run_id>/generated_app/`.
- Added a **run summary** (`run_summary.json`) and made the pipeline resilient to minor manifest formatting issues.
