# Troubleshooting

## 401 “invalid_api_key” but the key is valid

This usually means a **stale** `OPENAI_API_KEY` was already set in your shell and was not being overridden.
This project loads `.env` with override semantics; confirm your `.env` is correct in this folder and re-run.

### Manifest safety behavior

- Paths are applied under `generated_app/` and normalized (leading `generated_app/` is stripped if present).
- Dotfile paths are rejected.
- File size is capped (to avoid huge accidental outputs).
- If `content_mode="fenced_code"` is set but no fenced block is present, the pipeline writes the content literally and records a warning.

## Design notes

- Proposed changes discussion: `docs/proposed_changes_summary.md`

## Summary of steps taken (high level)

- Added **Pydantic output schemas** for `DesignPack`, `BuildPlan`, and `FileManifest`.
- Updated **agent/task config** to match the phase-gated workflow and pinned models to `gpt-4o-mini`.
- Made the runner **spec-file driven** and added robust `.env` loading (override to avoid stale keys).
- Implemented an **artifacts pipeline** that writes `spec_pack.json`, `design_pack.json`, `build_plan.json`, plus callback logs.
- Added **dynamic task execution** from `BuildPlan` producing `FileManifest`s, and applied manifests into `artifacts/<run_id>/generated_app/`.
- Added a **run summary** (`run_summary.json`) and made the pipeline resilient to minor manifest formatting issues.
