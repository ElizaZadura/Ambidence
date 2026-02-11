# Spec: Modular To-Do App (CLI) — v1 Trial Run

## Goal

Build a small, modular Python application that manages a personal to-do list. This is a trial run to validate the multi-agent workflow (spec → design → build → test), not a feature-complete product.

## Functional Requirements

1. The app must support these commands:
   - `add "<text>"` → adds a new task
   - `list` → shows tasks with IDs and status
   - `done <id>` → marks a task as completed
   - `remove <id>` → deletes a task
   - `help` → shows usage
2. Tasks must have:
   - integer ID (stable across runs)
   - text
   - status: `TODO` or `DONE`
   - created timestamp (ISO string is fine)
3. Data must persist between runs in a local file.

## Non-Functional Constraints

- Python 3.11+
- No external database (use a local file; JSON is preferred)
- Keep the code modular (not a single `app.py` blob)
- Clear separation between:
  - domain/model
  - storage/persistence
  - command parsing / CLI interface

## Acceptance Criteria

- Running `python -m todo_app help` prints usage.
- `add` then `list` shows the new task.
- `done` updates status correctly and persists.
- `remove` deletes the task and persists.
- Invalid commands or IDs return a helpful error message and exit with non-zero status.

## Out of Scope (v1)

- GUI
- Web API
- User accounts
- Tagging, priorities, due dates
- Search, sorting, filtering beyond basic listing

## Open Questions

- None for v1. Make reasonable defaults.
