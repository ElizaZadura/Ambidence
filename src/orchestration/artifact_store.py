from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Any, Dict


@dataclass(frozen=True)
class RunArtifacts:
    run_id: str
    artifacts_dir: Path
    generated_app_dir: Path


_MARKERS = ("pyproject.toml", ".git")


def project_root_from_src_file(src_file: str) -> Path:
    """Walk up from *src_file* until we find a project-root marker."""
    current = Path(src_file).resolve().parent
    for parent in (current, *current.parents):
        if any((parent / m).exists() for m in _MARKERS):
            return parent
    raise RuntimeError(
        f"Could not locate project root from {src_file} "
        f"(looked for {_MARKERS})"
    )


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def init_run_artifacts(project_root: Path, run_id: str) -> RunArtifacts:
    artifacts_dir = project_root / "artifacts" / run_id
    generated_app_dir = artifacts_dir / "generated_app"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    generated_app_dir.mkdir(parents=True, exist_ok=True)
    return RunArtifacts(run_id=run_id, artifacts_dir=artifacts_dir, generated_app_dir=generated_app_dir)


def write_spec(artifacts_dir: Path, spec_text: str, filename: str = "spec.md") -> Path:
    out = artifacts_dir / filename
    out.write_text(spec_text, encoding="utf-8")
    return out


def ensure_callbacks_log(artifacts_dir: Path, filename: str = "callbacks.log.jsonl") -> Path:
    out = artifacts_dir / filename
    if not out.exists():
        out.write_text("", encoding="utf-8")
    return out


def append_callback(callbacks_log: Path, payload: Dict[str, Any]) -> None:
    callbacks_log.parent.mkdir(parents=True, exist_ok=True)
    with callbacks_log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

