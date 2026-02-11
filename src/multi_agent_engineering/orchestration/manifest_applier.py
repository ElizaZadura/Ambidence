from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path

from multi_agent_engineering.models.file_manifest import FileManifest




BASELINE_FILES = {
    "pyproject.toml",
    "src/app/__init__.py",
    "src/app/__main__.py",
    "tests/test_smoke.py",
}
_FENCE_RE = re.compile(r"```[^\n]*\n([\s\S]*?)\n```", re.MULTILINE)


class ManifestApplyError(Exception):
    pass


@dataclass(frozen=True)
class ApplyResult:
    written: list[Path]
    warnings: list[str]


def _is_unsafe_relpath(p: str) -> bool:
    # Reject absolute paths, drive letters, home, and traversal.
    if not p or p.strip() != p:
        return True
    if p.startswith(("/", "\\", "~")):
        return True
    if ":" in p.split("/")[0].split("\\")[0]:
        return True
    parts = Path(p).parts
    if any(part in ("..",) for part in parts):
        return True
    return False


def _has_dotfile_segment(p: str) -> bool:
    return any(part.startswith(".") for part in Path(p).parts)


def _normalize_manifest_path(p: str) -> str:
    """
    Normalize common prefixes from model output.
    Our target_root is already artifacts/<run_id>/generated_app, but agents often
    emit paths starting with 'generated_app/...'. Strip that prefix if present.
    """
    p2 = p.replace("\\", "/")
    if p2.startswith("generated_app/"):
        return p2[len("generated_app/") :]
    return p2


def _extract_fenced_code(content: str) -> tuple[str, bool]:
    m = _FENCE_RE.search(content)
    if not m:
        # Be forgiving: some agents may set fenced_code without actually adding fences.
        # In that case, fall back to writing literal content so runs don't hard-fail.
        return content, True
    return m.group(1), False


def apply_manifest(manifest: FileManifest, target_root: Path, *, max_bytes: int = 200_000) -> ApplyResult:
    """
    Apply a FileManifest under target_root (e.g. artifacts/<run_id>/generated_app).
    Returns list of written file paths (absolute).
    """
    target_root = target_root.resolve()
    written: list[Path] = []
    warnings: list[str] = []

    for entry in manifest.files:
        rel_path = _normalize_manifest_path(entry.path)
        if _is_unsafe_relpath(rel_path):
            raise ManifestApplyError(f"Unsafe path in manifest: {entry.path!r}")
        if _has_dotfile_segment(rel_path):
            raise ManifestApplyError(f"Dotfile paths are not allowed in manifest: {entry.path!r}")
        if rel_path in BASELINE_FILES:
            warnings.append(f"{entry.path}: baseline file write skipped")
            continue

        out_path = (target_root / rel_path).resolve()
        if target_root not in out_path.parents and out_path != target_root:
            raise ManifestApplyError(f"Path escapes target root: {entry.path!r}")

        out_path.parent.mkdir(parents=True, exist_ok=True)

        if out_path.exists() and not entry.overwrite:
            continue

        content = entry.content
        if entry.content_mode == "fenced_code":
            content, fell_back = _extract_fenced_code(content)
            if fell_back:
                warnings.append(f"{entry.path}: content_mode=fenced_code but no fenced block found; wrote literal content")

        if len(content.encode("utf-8")) > max_bytes:
            raise ManifestApplyError(f"File too large in manifest: {entry.path!r} (> {max_bytes} bytes)")

        out_path.write_text(content, encoding="utf-8")
        written.append(out_path)

    return ApplyResult(written=written, warnings=warnings)

