from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

# Pydantic v2 deprecates root_validator; keep v1/v2 compatibility.
try:  # pydantic>=2
    from pydantic import model_validator  # type: ignore

    _HAS_MODEL_VALIDATOR = True
except Exception:  # pragma: no cover
    from pydantic import root_validator  # type: ignore

    _HAS_MODEL_VALIDATOR = False


class PlannedTask(BaseModel):
    task_id: str
    owner_agent: str
    description: str
    acceptance_criteria: List[str] = Field(default_factory=list)
    expected_deliverables: List[str] = Field(default_factory=list)


class BuildPlan(BaseModel):
    """
    Structured output of the `plan_execution` phase.

    v1 constraint: planned_tasks must contain at most 3 tasks.
    """

    run_id: str = ""
    planned_tasks: List[PlannedTask] = Field(default_factory=list)
    test_strategy: List[str] = Field(default_factory=list)
    integration_notes: List[str] = Field(default_factory=list)

    if _HAS_MODEL_VALIDATOR:

        @model_validator(mode="after")
        def _validate_task_cap(self):  # type: ignore[no-redef]
            if len(self.planned_tasks) > 3:
                raise ValueError("BuildPlan.planned_tasks must contain at most 3 tasks (v1 constraint).")
            return self

    else:

        @root_validator(skip_on_failure=True)
        def _validate_task_cap(cls, values):  # type: ignore[no-redef]
            planned_tasks = values.get("planned_tasks") or []
            if len(planned_tasks) > 3:
                raise ValueError("BuildPlan.planned_tasks must contain at most 3 tasks (v1 constraint).")
            return values

