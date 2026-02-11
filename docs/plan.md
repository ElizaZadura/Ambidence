# CrewAI Minimal Multi‑Agent Engineering Plan (v1)

## Goal

Build a **spec‑driven engineering crew** that can take a requirements spec and produce a modular, runnable application.

This version is intentionally **minimal**: to keep complexity contained. Advanced orchestration features are included only where they teach something concrete.

---

## Agents (existing)

- **engineering_lead**
- **core_domain_engineer**
- **ui_engineer**
- **test_infra_engineer**

No new agents added in v1.

---

## Core Workflow (Spine)

### 1. Spec Intake (Gate 1)

- **Task:** `spec_intake`
- **Owner:** engineering_lead
- **Output:** `SpecPack` (structured / Pydantic)

**Purpose:**

- Clarify scope and intent
- Surface constraints and open questions
- Prevent premature design or coding

No downstream work starts without an approved SpecPack.

---

### 2. Design & Contracts (Gate 2)

- **Task:** `design`
- **Owner:** core_domain_engineer
- **Input:** SpecPack
- **Output:** `DesignPack` (structured / Pydantic)

**Purpose:**

- Define architecture and module boundaries
- Specify interfaces / contracts
- Identify ownership and risks

**Hard rule:** No implementation code in this task.

---

## Dynamic Task Creation (Kept, but Scoped)

### 3. Execution Planning

- **Task:** `plan_execution`
- **Owner:** engineering_lead
- **Input:** DesignPack
- **Output:** `BuildPlan` (structured)

**BuildPlan contains:**

- A **maximum of 3 implementation tasks**
- Each task specifies:
  - task_id
  - owner_agent
  - description
  - acceptance_criteria
  - expected deliverables

This task is the **only place** where dynamic task creation is introduced.

---

## Dynamically Generated Tasks

From BuildPlan, the system instantiates real tasks, typically:

- **core_backend** → core_domain_engineer
- **ui** → ui_engineer
- **tests_infra** → test_infra_engineer

Each task:

- Implements only its assigned slice
- Is evaluated against its acceptance criteria

---

## Callbacks (Minimal)

Each dynamically created task has **one callback**:

- Trigger: task completion
- Action:
  - Log task_id
  - Success / failure
  - Produced artifacts or paths
  - Any blocking issues

Purpose: learn callback mechanics without building an orchestration framework.

---

## Explicitly Deferred (v2 / Project Phase)

Not part of v1:

- Recursive task generation
- Iterative planning loops
- Budget enforcement logic
- Tool integrations
- Advanced agent negotiation

These are postponed to keep the course exercise focused.

---

## Summary

v1 delivers:

- Structured outputs (SpecPack, DesignPack, BuildPlan)
- Clear role separation
- One real phase gate
- Dynamic task creation + callbacks (minimal, controlled)

Everything else is intentionally deferred.
