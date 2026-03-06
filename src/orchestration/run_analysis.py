"""Post-run analysis: spec compliance, code quality, and runnability checks."""

from __future__ import annotations

import ast
import json
import logging
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from orchestration.artifact_store import RunArtifacts, read_json, write_json

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class _Check:
    """Single pass/fail/warning check result."""

    __slots__ = ("passed", "label", "detail")

    def __init__(self, passed: bool, label: str, detail: str = "") -> None:
        self.passed = passed
        self.label = label
        self.detail = detail

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"passed": self.passed, "label": self.label}
        if self.detail:
            d["detail"] = self.detail
        return d


class _Section:
    """Named group of checks."""

    __slots__ = ("name", "checks")

    def __init__(self, name: str) -> None:
        self.name = name
        self.checks: List[_Check] = []

    def add(self, passed: bool, label: str, detail: str = "") -> None:
        self.checks.append(_Check(passed, label, detail))

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "checks": [c.to_dict() for c in self.checks],
        }


# ---------------------------------------------------------------------------
# Individual analysis passes
# ---------------------------------------------------------------------------

def _check_spec_compliance(
    generated_app_dir: Path,
    spec_pack: Dict[str, Any],
    design_pack: Dict[str, Any],
) -> _Section:
    sec = _Section("Spec Compliance")

    all_py_text = _read_all_py(generated_app_dir)

    for req in spec_pack.get("functional_requirements", []):
        keywords = _extract_keywords(req)
        found = any(kw in all_py_text for kw in keywords)
        sec.add(found, f"Functional: {req}")

    for req in spec_pack.get("acceptance_criteria", []):
        keywords = _extract_keywords(req)
        found = any(kw in all_py_text for kw in keywords)
        sec.add(found, f"Acceptance: {req}")

    return sec


def _check_design_adherence(
    generated_app_dir: Path,
    design_pack: Dict[str, Any],
) -> _Section:
    sec = _Section("Design Contract Adherence")

    all_py_text = _read_all_py(generated_app_dir)

    for model in design_pack.get("data_models", []):
        model_name = model.get("name", "?")
        if model_name.lower() in all_py_text:
            sec.add(True, f"Data model `{model_name}` present")
        else:
            sec.add(False, f"MISSING data model `{model_name}`")

        for field_spec in model.get("fields", []):
            field_name = field_spec.split(":")[0].strip()
            if field_name.lower() in all_py_text:
                sec.add(True, f"`{model_name}` has field `{field_name}`")
            else:
                sec.add(False, f"MISSING `{model_name}` field `{field_name}`")

    return sec


def _check_code_quality(generated_app_dir: Path) -> _Section:
    sec = _Section("Code Quality")

    py_files = sorted(generated_app_dir.rglob("*.py"))
    py_files = [p for p in py_files if "__pycache__" not in p.parts]

    # --- AST parse check ---
    parsed_trees: Dict[Path, ast.Module] = {}
    for pf in py_files:
        try:
            tree = ast.parse(pf.read_text(encoding="utf-8"), filename=str(pf))
            parsed_trees[pf] = tree
        except SyntaxError as e:
            sec.add(False, f"Syntax error in `{pf.relative_to(generated_app_dir)}`", str(e))

    if not any(not c.passed for c in sec.checks):
        sec.add(True, "All files parse without syntax errors")

    # --- Duplicate symbol detection ---
    symbols: Dict[str, List[str]] = defaultdict(list)
    for pf, tree in parsed_trees.items():
        rel = str(pf.relative_to(generated_app_dir))
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    symbols[node.name].append(rel)

    for name, locations in sorted(symbols.items()):
        if len(locations) > 1:
            unique = sorted(set(locations))
            if len(unique) > 1:
                sec.add(False, f"Duplicate symbol `{name}`", f"Found in: {', '.join(unique)}")

    if not any("Duplicate" in c.label for c in sec.checks):
        sec.add(True, "No duplicate symbols across files")

    # --- Dead file detection ---
    import_targets: set[str] = set()
    for tree in parsed_trees.values():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_targets.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    parts = node.module.split(".")
                    import_targets.update(parts)

    for pf in py_files:
        rel = pf.relative_to(generated_app_dir)
        stem = pf.stem
        if stem.startswith("__") or any(p.startswith("test") for p in rel.parts):
            continue
        if stem not in import_targets:
            sec.add(False, f"Dead file: `{rel}`", "Not imported by any other module")

    if not any("Dead file" in c.label for c in sec.checks):
        sec.add(True, "No dead files detected")

    return sec


def _check_runnability(generated_app_dir: Path) -> _Section:
    sec = _Section("Runnability")

    app_dir = generated_app_dir.resolve()
    src_dir = app_dir / "src"
    env = {**__import__("os").environ, "PYTHONPATH": str(src_dir)}

    commands = {
        "--help": [sys.executable, "-m", "app", "--help"],
        "--demo": [sys.executable, "-m", "app", "--demo"],
        "tests": [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
    }

    for label, cmd in commands.items():
        try:
            r = subprocess.run(
                cmd,
                cwd=str(app_dir),
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
            )
            if r.returncode == 0:
                sec.add(True, f"`{label}` exits 0")
            else:
                detail = (r.stderr or r.stdout or "")[:300].strip()
                sec.add(False, f"`{label}` exits {r.returncode}", detail)
        except Exception as e:
            sec.add(False, f"`{label}` failed to run", str(e))

    return sec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset(
    "the a an is are was were be been being have has had do does did "
    "will would shall should may might can could must need dare ought "
    "and or but nor not no so if then else when while for to of in on "
    "at by from with as into through during before after above below "
    "between out off over under again further once each every all both "
    "few more most other some such only own same than too very that this "
    "it its".split()
)


def _extract_keywords(text: str) -> List[str]:
    """Pull meaningful lowercase tokens from a requirement string."""
    tokens = []
    for word in text.lower().split():
        cleaned = "".join(c for c in word if c.isalnum() or c == "_")
        if cleaned and cleaned not in _STOP_WORDS and len(cleaned) > 2:
            tokens.append(cleaned)
    return tokens


def _read_all_py(directory: Path) -> str:
    """Concatenate all .py file contents into a single lowercase string for keyword search."""
    parts: List[str] = []
    for pf in sorted(directory.rglob("*.py")):
        if "__pycache__" not in pf.parts:
            try:
                parts.append(pf.read_text(encoding="utf-8").lower())
            except Exception:
                pass
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------

def _render_markdown(run_id: str, sections: List[_Section]) -> str:
    lines = [f"# Run Analysis: {run_id}", ""]

    for sec in sections:
        lines.append(f"## {sec.name}")
        lines.append("")
        for chk in sec.checks:
            mark = "x" if chk.passed else " "
            prefix = "" if chk.passed else ("" if "MISSING" in chk.label else "WARNING: ")
            line = f"- [{mark}] {prefix}{chk.label}"
            if chk.detail and not chk.passed:
                line += f"  — {chk.detail}"
            lines.append(line)
        lines.append("")

    lines.append("## Manual Notes")
    lines.append("")
    lines.append("<!-- Add your observations below -->")
    lines.append("")
    return "\n".join(lines)


def _build_json(run_id: str, sections: List[_Section]) -> Dict[str, Any]:
    total_passed = sum(s.passed_count for s in sections)
    total_failed = sum(s.failed_count for s in sections)
    return {
        "run_id": run_id,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "sections": [s.to_dict() for s in sections],
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def analyze_run(run_artifacts: RunArtifacts) -> Dict[str, Any]:
    """Run all analysis checks and write reports. Returns the JSON summary dict."""
    artifacts_dir = run_artifacts.artifacts_dir
    generated_app_dir = run_artifacts.generated_app_dir
    run_id = run_artifacts.run_id

    spec_pack: Dict[str, Any] = {}
    design_pack: Dict[str, Any] = {}
    spec_path = artifacts_dir / "spec_pack.json"
    design_path = artifacts_dir / "design_pack.json"

    if spec_path.exists():
        try:
            spec_pack = read_json(spec_path)
        except Exception as e:
            log.warning("Could not read spec_pack.json: %s", e)

    if design_path.exists():
        try:
            design_pack = read_json(design_path)
        except Exception as e:
            log.warning("Could not read design_pack.json: %s", e)

    sections: List[_Section] = []

    if spec_pack:
        sections.append(_check_spec_compliance(generated_app_dir, spec_pack, design_pack))

    if design_pack:
        sections.append(_check_design_adherence(generated_app_dir, design_pack))

    sections.append(_check_code_quality(generated_app_dir))
    sections.append(_check_runnability(generated_app_dir))

    analysis = _build_json(run_id, sections)

    write_json(artifacts_dir / "run_analysis.json", analysis)

    md = _render_markdown(run_id, sections)
    (artifacts_dir / "run_analysis.md").write_text(md, encoding="utf-8")

    log.info(
        "Run analysis complete: %d passed, %d failed",
        analysis["total_passed"],
        analysis["total_failed"],
    )
    return analysis
