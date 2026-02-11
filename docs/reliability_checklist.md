# Reliability checklist (core pipeline)

Goal

- The pipeline should be predictable: same inputs -> same artifact structure, failures are explicit, and provenance is complete.

Checklist

1) Deterministic outputs
   - Enforce a single owner for baseline files (pyproject.toml, src/app/__init__.py, src/app/__main__.py, tests/test_smoke.py).
   - Avoid last-writer wins; log when a manifest attempts to overwrite baseline files.

2) Schema and contract validation
   - Validate BuildPlan and FileManifest strictly before use.
   - Enforce task_id consistency between planned tasks and returned manifests.
   - Reject unknown or malformed fields early with clear errors.

3) Failure handling
   - Always write run_summary.json even if one or more tasks fail.
   - Capture failure payloads with task_id, agent, and error details.

4) Provenance logging
   - Record agent id, model, prompt hash, input hash, and output hash for each task.
   - Keep callbacks.log.jsonl as the single source for task-level provenance.

5) Idempotent apply
   - Re-applying the same artifacts should not corrupt or multiply files.
   - Prefer deterministic overwrite rules or explicit skips with warnings.

6) Baseline golden runs
   - Maintain one or two known-good specs.
   - Snapshot expected artifact structure to detect regressions.

Notes

- This list is a stability gate for future artifact lineage work (visual tracing, diffing, etc.).
- If the pipeline violates any of the above, pause traceability features until fixed.
