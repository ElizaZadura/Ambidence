#!/usr/bin/env python
import os
import sys
import warnings

from pathlib import Path

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def _project_root() -> Path:
    # main.py lives at: <project>/src/multi_agent_engineering/main.py
    from multi_agent_engineering.orchestration.artifact_store import project_root_from_src_file
    return project_root_from_src_file(__file__)


def _load_dotenv(dotenv_path: Path) -> None:
    """
    Load .env early and deterministically.

    - Prefer python-dotenv if available (it correctly handles quoting/escaping).
    - Always override existing env vars so stale keys don't win.
    """
    if not dotenv_path.exists():
        return

    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(dotenv_path=dotenv_path, override=True)
        return
    except Exception:
        pass

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            os.environ[key] = value


def _resolve_spec_path() -> Path:
    """
    Resolve a spec file path from, in order:
    - CLI arg (first positional)
    - env var SPEC_FILE
    - default files in project root: spec.md, spec.txt
    """
    # Support explicit flag: --spec-file PATH (or -s PATH)
    for i, arg in enumerate(sys.argv[1:], start=1):
        if arg in ("--spec-file", "--spec", "-s"):
            if i + 1 >= len(sys.argv):
                raise FileNotFoundError(f"{arg} provided but no path value given")
            return Path(sys.argv[i + 1]).expanduser()

    if len(sys.argv) >= 2 and sys.argv[1].strip() and not sys.argv[1].startswith("-"):
        return Path(sys.argv[1]).expanduser()

    env_path = os.environ.get("SPEC_FILE", "").strip()
    if env_path:
        return Path(env_path).expanduser()

    root = _project_root()
    for candidate in ("spec.md", "spec.txt"):
        p = root / candidate
        if p.exists():
            return p

    raise FileNotFoundError(
        "No spec file provided. Pass a path as the first argument, set SPEC_FILE, "
        "or create spec.md/spec.txt in the project root."
    )


def _prepare_run_context(
    *,
    root: Path,
    spec_text: str | None,
    spec_path: Path | None,
    trigger_payload: dict | None = None,
) -> tuple:
    from multi_agent_engineering.orchestration.artifact_store import (
        ensure_callbacks_log,
        init_run_artifacts,
        new_run_id,
        write_spec,
    )

    run_id = new_run_id()
    run_artifacts = init_run_artifacts(root, run_id=run_id)
    if spec_text:
        write_spec(run_artifacts.artifacts_dir, spec_text, filename="spec.md")
    ensure_callbacks_log(run_artifacts.artifacts_dir)

    inputs = {
        "spec": spec_text or "",
        "spec_path": str(spec_path) if spec_path else "",
        "run_id": run_id,
        # Used by tasks.yaml output_file paths.
        "artifacts_dir": run_artifacts.artifacts_dir.as_posix(),
    }
    if trigger_payload is not None:
        inputs["crewai_trigger_payload"] = trigger_payload

    return run_artifacts, inputs


def run():
    """
    Run the crew.
    """
    root = _project_root()
    _load_dotenv(root / ".env")

    spec_path = _resolve_spec_path()
    spec_text = spec_path.read_text(encoding="utf-8")

    from multi_agent_engineering.crew import MultiAgentEngineering
    from multi_agent_engineering.orchestration.pipeline import run_full_pipeline

    run_artifacts, inputs = _prepare_run_context(
        root=root, spec_text=spec_text, spec_path=spec_path
    )

    try:
        run_full_pipeline(
            crew_factory=MultiAgentEngineering,
            run_artifacts=run_artifacts,
            inputs=inputs,
        )
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    # For training, use the same spec-driven inputs as `run()`.
    root = _project_root()
    _load_dotenv(root / ".env")
    spec_path = _resolve_spec_path()
    spec_text = spec_path.read_text(encoding="utf-8")

    from multi_agent_engineering.crew import MultiAgentEngineering

    _, inputs = _prepare_run_context(root=root, spec_text=spec_text, spec_path=spec_path)
    try:
        MultiAgentEngineering().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    root = _project_root()
    _load_dotenv(root / ".env")
    from multi_agent_engineering.crew import MultiAgentEngineering
    try:
        MultiAgentEngineering().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    # For testing, use the same spec-driven inputs as `run()`.
    root = _project_root()
    _load_dotenv(root / ".env")
    spec_path = _resolve_spec_path()
    spec_text = spec_path.read_text(encoding="utf-8")

    from multi_agent_engineering.crew import MultiAgentEngineering

    _, inputs = _prepare_run_context(root=root, spec_text=spec_text, spec_path=spec_path)

    try:
        MultiAgentEngineering().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    root = _project_root()
    _load_dotenv(root / ".env")

    # Prefer spec content if provided in trigger payload.
    spec_text = trigger_payload.get("spec")
    spec_path = trigger_payload.get("spec_path") or trigger_payload.get("spec_file")
    if spec_text is None and spec_path:
        spec_text = Path(spec_path).expanduser().read_text(encoding="utf-8")

    from multi_agent_engineering.crew import MultiAgentEngineering

    _, inputs = _prepare_run_context(
        root=root,
        spec_text=spec_text,
        spec_path=Path(spec_path).expanduser() if spec_path else None,
        trigger_payload=trigger_payload,
    )

    try:
        result = MultiAgentEngineering().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
