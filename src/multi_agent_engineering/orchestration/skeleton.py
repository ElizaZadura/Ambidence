from __future__ import annotations

from pathlib import Path


def ensure_python_skeleton(generated_app_dir: Path) -> list[Path]:
    """
    Ensure a minimal runnable Python skeleton exists under generated_app_dir.
    Does not overwrite existing files; only creates missing ones.
    """
    generated_app_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    def write_if_missing(rel: str, content: str) -> None:
        p = (generated_app_dir / rel).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            return
        p.write_text(content, encoding="utf-8")
        written.append(p)

    write_if_missing(
        "pyproject.toml",
        "\n".join(
            [
                '[project]',
                'name = "generated_app"',
                'version = "0.1.0"',
                'requires-python = ">=3.10,<3.14"',
                "",
                '[tool.pytest.ini_options]',
                'pythonpath = ["src"]',
                "",
            ]
        )
        + "\n",
    )

    write_if_missing("src/app/__init__.py", "__all__ = []\n")

    write_if_missing(
        "src/app/domain.py",
        "\n".join(
            [
                "from __future__ import annotations",
                "",
                "from dataclasses import dataclass",
                "",
                "",
                "@dataclass",
                "class Task:",
                "    id: int",
                "    text: str",
                "    done: bool = False",
                "",
                "",
                "class TaskManager:",
                "    def __init__(self) -> None:",
                "        self._tasks: dict[int, Task] = {}",
                "        self._next_id = 1",
                "",
                "    def add(self, text: str) -> Task:",
                "        t = Task(id=self._next_id, text=text, done=False)",
                "        self._tasks[t.id] = t",
                "        self._next_id += 1",
                "        return t",
                "",
                "    def list(self) -> list[Task]:",
                "        return [self._tasks[k] for k in sorted(self._tasks.keys())]",
                "",
                "    def done(self, task_id: int) -> None:",
                "        if task_id not in self._tasks:",
                "            raise KeyError(task_id)",
                "        self._tasks[task_id].done = True",
                "",
                "    def remove(self, task_id: int) -> None:",
                "        if task_id not in self._tasks:",
                "            raise KeyError(task_id)",
                "        del self._tasks[task_id]",
                "",
            ]
        )
        + "\n",
    )

    write_if_missing(
        "src/app/services.py",
        "\n".join(
            [
                "from __future__ import annotations",
                "",
                "import json",
                "from pathlib import Path",
                "",
                "from app.domain import Task, TaskManager",
                "",
                "",
                "def load(manager: TaskManager, storage_path: Path) -> None:",
                "    if not storage_path.exists():",
                "        return",
                "    data = json.loads(storage_path.read_text(encoding='utf-8'))",
                "    tasks = data.get('tasks', []) if isinstance(data, dict) else []",
                "    # Rebuild manager deterministically.",
                "    for t in tasks:",
                "        task = Task(id=int(t['id']), text=str(t['text']), done=bool(t.get('done', False)))",
                "        manager._tasks[task.id] = task  # noqa: SLF001 (intentionally minimal)",
                "        manager._next_id = max(manager._next_id, task.id + 1)  # noqa: SLF001",
                "",
                "",
                "def save(manager: TaskManager, storage_path: Path) -> None:",
                "    tasks = [{'id': t.id, 'text': t.text, 'done': t.done} for t in manager.list()]",
                "    storage_path.parent.mkdir(parents=True, exist_ok=True)",
                "    storage_path.write_text(json.dumps({'tasks': tasks}, indent=2), encoding='utf-8')",
                "",
            ]
        )
        + "\n",
    )

    write_if_missing(
        "src/app/ui.py",
        "\n".join(
            [
                "from __future__ import annotations",
                "",
                "from pathlib import Path",
                "",
                "from app.domain import TaskManager",
                "from app.services import load, save",
                "",
                "",
                "def run_demo(storage_path: Path) -> str:",
                "    mgr = TaskManager()",
                "    load(mgr, storage_path)",
                "    t = mgr.add('demo task')",
                "    mgr.done(t.id)",
                "    save(mgr, storage_path)",
                "    return f'Demo OK: added+completed task {t.id}'",
                "",
            ]
        )
        + "\n",
    )

    write_if_missing(
        "src/app/__main__.py",
        "\n".join(
            [
                "from __future__ import annotations",
                "",
                "import argparse",
                "from pathlib import Path",
                "",
                "from app.ui import run_demo",
                "",
                "",
                "def main(argv: list[str] | None = None) -> int:",
                "    parser = argparse.ArgumentParser(prog='app', description='Generated app skeleton')",
                "    parser.add_argument('--demo', action='store_true', help='Run a small end-to-end demo')",
                "    parser.add_argument('--storage', default='data/tasks.json', help='Path to JSON task storage')",
                "    args = parser.parse_args(argv)",
                "",
                "    if args.demo:",
                "        msg = run_demo(Path(args.storage))",
                "        print(msg)",
                "        return 0",
                "",
                "    parser.print_help()",
                "    return 0",
                "",
                "",
                "if __name__ == '__main__':",
                "    raise SystemExit(main())",
                "",
            ]
        )
        + "\n",
    )

    write_if_missing(
        "tests/test_smoke.py",
        "\n".join(
            [
                "import subprocess",
                "import sys",
                "import unittest",
                "from pathlib import Path",
                "",
                "",
                "class TestSmoke(unittest.TestCase):",
                "    def test_help(self):",
                "        root = Path(__file__).resolve().parents[1]",
                "        r = subprocess.run([sys.executable, '-m', 'app', '--help'], cwd=root, capture_output=True, text=True)",
                "        self.assertEqual(r.returncode, 0)",
                "        self.assertIn('usage:', r.stdout.lower())",
                "",
                "    def test_demo(self):",
                "        root = Path(__file__).resolve().parents[1]",
                "        r = subprocess.run([sys.executable, '-m', 'app', '--demo'], cwd=root, capture_output=True, text=True)",
                "        self.assertEqual(r.returncode, 0)",
                "        self.assertIn('demo ok', r.stdout.lower())",
                "",
                "",
                "if __name__ == '__main__':",
                "    unittest.main()",
                "",
            ]
        )
        + "\n",
    )

    return written

