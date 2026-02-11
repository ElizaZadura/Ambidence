from __future__ import annotations

from datetime import datetime, timezone
import re
from pathlib import Path
from typing import Any, Dict

from crewai import Agent, Crew, Process, Task

from multi_agent_engineering.models.build_plan import BuildPlan
from multi_agent_engineering.models.file_manifest import FileManifest
from multi_agent_engineering.orchestration.artifact_store import (
    RunArtifacts,
    append_callback,
    ensure_callbacks_log,
    read_json,
    write_json,
)
from multi_agent_engineering.orchestration.manifest_applier import apply_manifest
from multi_agent_engineering.orchestration.skeleton import ensure_python_skeleton


def _norm_agent_token(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def _resolve_owner_agent_id(owner_agent: str, agent_map: Dict[str, Agent]) -> str:
    """
    Accept either an agent id (preferred) or a role-ish string like 'Domain Engineer'.
    Returns a canonical agent id key from agent_map.
    """
    if owner_agent in agent_map:
        return owner_agent

    token = _norm_agent_token(owner_agent)
    if token in agent_map:
        return token

    # Common aliases / near-misses from LLM outputs.
    aliases: Dict[str, str] = {
        "domain_engineer": "core_domain_engineer",
        "service_engineer": "core_domain_engineer",
        "backend_engineer": "core_domain_engineer",
        "core_backend_engineer": "core_domain_engineer",
        "frontend_engineer": "ui_engineer",
        "ui": "ui_engineer",
        "infra_engineer": "test_infra_engineer",
        "infrastructure_engineer": "test_infra_engineer",
        "devops_engineer": "test_infra_engineer",
        "platform_engineer": "test_infra_engineer",
        "storage_engineer": "test_infra_engineer",
        "tests_engineer": "test_infra_engineer",
        "test_engineer": "test_infra_engineer",
        "qa_engineer": "test_infra_engineer",
        "engineering_manager": "engineering_lead",
        "tech_lead": "engineering_lead",
    }
    if token in aliases and aliases[token] in agent_map:
        return aliases[token]

    # Heuristic mapping (last resort) to keep runs moving on minor naming drift.
    if "test" in token or "qa" in token:
        return "test_infra_engineer"
    if "infra" in token or "devops" in token or "ops" in token or "platform" in token or "storage" in token:
        return "test_infra_engineer"
    if "ui" in token or "front" in token:
        return "ui_engineer"
    if "domain" in token or "service" in token or "backend" in token or "core" in token:
        return "core_domain_engineer"
    if "lead" in token or "manager" in token:
        return "engineering_lead"

    # Match against agent.role values (configured in agents.yaml), e.g. 'Domain Engineer.'
    role_index: Dict[str, str] = {}
    for agent_id, agent in agent_map.items():
        role_index[_norm_agent_token(getattr(agent, "role", ""))] = agent_id

    if token in role_index:
        return role_index[token]

    raise ValueError(
        f"Unknown owner_agent in BuildPlan: {owner_agent!r}. "
        f"Use one of: {', '.join(sorted(agent_map.keys()))}"
    )


def run_spine(
    *,
    crew_factory: Any,
    inputs: Dict[str, Any],
    run_artifacts: RunArtifacts,
) -> BuildPlan:
    """
    Execute the static spine tasks using the existing CrewBase task definitions
    (spec_intake -> design -> plan_execution). We rely on tasks.yaml output_file
    paths to persist the JSON artifacts in artifacts_dir.
    """
    ensure_callbacks_log(run_artifacts.artifacts_dir)

    crew_base = crew_factory()
    lead = crew_base.engineering_lead()
    designer = crew_base.core_domain_engineer()

    spec_task = crew_base.spec_intake_task()
    design_task = crew_base.design_task()
    plan_task = crew_base.plan_execution_task()

    spine = Crew(
        agents=[lead, designer],
        tasks=[spec_task, design_task, plan_task],
        process=Process.sequential,
        verbose=True,
    )
    spine.kickoff(inputs=inputs)

    build_plan_path = Path(inputs["artifacts_dir"]) / "build_plan.json"
    build_plan_data = read_json(build_plan_path)
    build_plan = BuildPlan.model_validate(build_plan_data)  # pydantic v2; works in your env
    # Always use the pipeline run_id for consistency with artifacts/<run_id>/.
    build_plan.run_id = str(inputs.get("run_id", ""))
    return build_plan


def run_dynamic_tasks(
    *,
    crew_factory: Any,
    inputs: Dict[str, Any],
    run_artifacts: RunArtifacts,
    build_plan: BuildPlan,
) -> tuple[list[FileManifest], list[dict]]:
    """
    Instantiate and execute dynamic tasks based on BuildPlan.planned_tasks.
    Each dynamic task must output a FileManifest (JSON).
    """
    crew_base = crew_factory()
    callbacks_log = ensure_callbacks_log(run_artifacts.artifacts_dir)

    # Map agent names -> Agent instances.
    agent_map: Dict[str, Agent] = {
        "engineering_lead": crew_base.engineering_lead(),
        "core_domain_engineer": crew_base.core_domain_engineer(),
        "ui_engineer": crew_base.ui_engineer(),
        "test_infra_engineer": crew_base.test_infra_engineer(),
    }

    manifests: list[FileManifest] = []
    task_results: list[dict] = []
    manifests_dir = run_artifacts.artifacts_dir / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)

    for planned in build_plan.planned_tasks:
        owner_agent_id = _resolve_owner_agent_id(planned.owner_agent, agent_map)
        agent = agent_map[owner_agent_id]

        dynamic_task = Task(
            description=(
                f"{planned.description}\n\n"
                "TARGET OUTPUT:\n"
                "- Generate a minimal runnable *Python* app skeleton under generated_app/.\n"
                "- Use Python files only (no .js/.ts). Keep docs minimal.\n"
                "- Required baseline files (coordinate across tasks):\n"
                "  - pyproject.toml\n"
                "  - src/app/__init__.py\n"
                "  - src/app/__main__.py  (supports: python -m app --help and --demo)\n"
                "  - tests/test_smoke.py  (unittest; python -m unittest)\n\n"
                "IMPORTANT OUTPUT FORMAT:\n"
                "- Output JSON ONLY matching the FileManifest schema exactly.\n"
                "- file contents are text; use content_mode=\"literal\" unless you include triple-backtick fenced code.\n"
                "- Only set content_mode=\"fenced_code\" if content actually includes a fenced code block.\n"
                "- Paths must be relative to generated_app/ (you may omit the 'generated_app/' prefix).\n"
            ),
            expected_output="JSON only (FileManifest).",
            agent=agent,
            output_pydantic=FileManifest,
            output_file=str((manifests_dir / f"{planned.task_id}.json").as_posix()),
        )

        manifest_path = manifests_dir / f"{planned.task_id}.json"
        try:
            c = Crew(agents=[agent], tasks=[dynamic_task], process=Process.sequential, verbose=True)
            c.kickoff(inputs=inputs)

            # Prefer reading the persisted manifest file for determinism.
            manifest_data = read_json(manifest_path)
            manifest = FileManifest.model_validate(manifest_data)
            if manifest.task_id != planned.task_id:
                raise ValueError(
                    f"Manifest task_id {manifest.task_id!r} does not match planned task_id {planned.task_id!r}"
                )
            manifests.append(manifest)

            append_callback(
                callbacks_log,
                {
                    "run_id": build_plan.run_id,
                    "task_id": planned.task_id,
                    "agent": owner_agent_id,
                    "status": "success",
                    "artifact_paths": [manifest_path.as_posix()],
                    "blocking_issues": [],
                },
            )
            task_results.append(
                {
                    "task_id": planned.task_id,
                    "agent": owner_agent_id,
                    "status": "success",
                    "manifest_path": manifest_path.as_posix(),
                    "blocking_issues": [],
                }
            )
        except Exception as e:
            blocking = [str(e)]
            append_callback(
                callbacks_log,
                {
                    "run_id": build_plan.run_id,
                    "task_id": planned.task_id,
                    "agent": owner_agent_id,
                    "status": "failed",
                    "artifact_paths": [manifest_path.as_posix()],
                    "blocking_issues": blocking,
                },
            )
            task_results.append(
                {
                    "task_id": planned.task_id,
                    "agent": owner_agent_id,
                    "status": "failed",
                    "manifest_path": manifest_path.as_posix(),
                    "blocking_issues": blocking,
                }
            )

    return manifests, task_results


def apply_manifests(
    *,
    run_artifacts: RunArtifacts,
    manifests: list[FileManifest],
) -> tuple[list[str], list[str]]:
    written: list[str] = []
    warnings: list[str] = []
    for m in manifests:
        result = apply_manifest(m, run_artifacts.generated_app_dir)
        written.extend([p.as_posix() for p in result.written])
        warnings.extend(result.warnings)
    return written, warnings


def run_full_pipeline(
    *,
    crew_factory: Any,
    run_artifacts: RunArtifacts,
    inputs: Dict[str, Any],
) -> Dict[str, Any]:
    started_at = datetime.now(timezone.utc).isoformat()
    run_id = inputs.get("run_id") or run_artifacts.run_id
    if not run_id:
        raise ValueError("inputs must include run_id (created in main.py)")
    if run_artifacts.run_id and run_artifacts.run_id != run_id:
        raise ValueError("inputs run_id does not match run_artifacts.run_id")

    build_plan = run_spine(crew_factory=crew_factory, inputs=inputs, run_artifacts=run_artifacts)
    manifests, task_results = run_dynamic_tasks(
        crew_factory=crew_factory, inputs=inputs, run_artifacts=run_artifacts, build_plan=build_plan
    )
    written, apply_warnings = apply_manifests(run_artifacts=run_artifacts, manifests=manifests)

    # Ensure baseline runnable Python skeleton exists (does not overwrite).
    skeleton_written = ensure_python_skeleton(run_artifacts.generated_app_dir)
    written.extend([p.as_posix() for p in skeleton_written])

    summary = {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "artifacts_dir": run_artifacts.artifacts_dir.as_posix(),
        "build_plan": {
            "planned_tasks": [t.model_dump() for t in build_plan.planned_tasks],  # type: ignore[attr-defined]
            "test_strategy": build_plan.test_strategy,
            "integration_notes": build_plan.integration_notes,
        },
        "dynamic_tasks": task_results,
        "written_files": sorted(set(written)),
        "warnings": apply_warnings,
    }
    write_json(run_artifacts.artifacts_dir / "run_summary.json", summary)
    return summary

