# Multi-Agent Engineering System: Master Plan

This document outlines the current engineering plan (v1) and the future strategic direction for the system.

---

## Part 1: Current Implementation Plan (v1)

### Goal

Build a **spec‑driven engineering crew** that can take a requirements spec and produce a modular, runnable application.

This version is intentionally **minimal**: to keep complexity contained. Advanced orchestration features are included only where they teach something concrete.

### Agents (existing)

- **engineering_lead**
- **core_domain_engineer**
- **ui_engineer**
- **test_infra_engineer**

No new agents added in v1.

### Core Workflow (Spine)

#### 1. Spec Intake (Gate 1)

- **Task:** `spec_intake`
- **Owner:** engineering_lead
- **Output:** `SpecPack` (structured / Pydantic)

**Purpose:**

- Clarify scope and intent
- Surface constraints and open questions
- Prevent premature design or coding

No downstream work starts without an approved SpecPack.

#### 2. Design & Contracts (Gate 2)

- **Task:** `design`
- **Owner:** core_domain_engineer
- **Input:** SpecPack
- **Output:** `DesignPack` (structured / Pydantic)

**Purpose:**

- Define architecture and module boundaries
- Specify interfaces / contracts
- Identify ownership and risks

**Hard rule:** No implementation code in this task.

### Dynamic Task Creation (Kept, but Scoped)

#### 3. Execution Planning

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

### Dynamically Generated Tasks

From BuildPlan, the system instantiates real tasks, typically:

- **core_backend** → core_domain_engineer
- **ui** → ui_engineer
- **tests_infra** → test_infra_engineer

Each task:

- Implements only its assigned slice
- Is evaluated against its acceptance criteria

### Callbacks (Minimal)

Each dynamically created task has **one callback**:

- Trigger: task completion
- Action:
  - Log task_id
  - Success / failure
  - Produced artifacts or paths
  - Any blocking issues

Purpose: learn callback mechanics without building an orchestration framework.

### Explicitly Deferred (v2 / Project Phase)

Not part of v1:

- Recursive task generation
- Iterative planning loops
- Budget enforcement logic
- Tool integrations
- Advanced agent negotiation

These are postponed to keep the course exercise focused.

### Summary of v1

v1 delivers:

- Structured outputs (SpecPack, DesignPack, BuildPlan)
- Clear role separation
- One real phase gate
- Dynamic task creation + callbacks (minimal, controlled)

Everything else is intentionally deferred.

---

## Part 2: Future Directions & Vision

> This section captures *future-facing ideas* and intentional non-goals. It is explicitly **not** a backlog to execute immediately. The purpose is to preserve thinking without forcing premature design or implementation.

### 1. Core Trajectory (Already in Motion)

#### 1.1 Spec → App as a First-Class Capability

**Goal**
The system accepts a written specification and produces a runnable software skeleton or application.

**Key characteristics**

- Spec is the *single source of intent*
- Agents collaborate through **structured artifacts**, not shared memory
- Pipeline enforces:
  - scope discipline
  - explicit ownership
  - verifiable outputs

**Status**
This is already partially implemented and validated. Further work here is refinement, not discovery.

### 2. Artifact Lineage & Traceability (High-Leverage, High-Complexity)

> *This is a second-order system built **on top of** the core pipeline.*

#### 2.1 Visual Artifact Tracing

**Idea**
Make it possible to visually inspect:

- which agent produced which artifact
- from which inputs
- using which model
- under which prompt + constraints

Think:

- timeline / graph view
- artifacts as nodes
- agent + model metadata as edges

**Why this matters**

- Debugging agentic systems is otherwise opaque
- Enables learning-by-comparison across runs
- Turns LLM behavior into something inspectable, not mystical

**Explicit complexity warning**
This is *not* just a UI problem. It requires:

- consistent metadata contracts
- stable run identifiers
- careful separation of content vs provenance

This should not be attempted until the core pipeline is boringly reliable.

### 3. Comparative Runs & Diffing (Emergent, Not Yet Designed)

#### 3.1 Cross-Run Comparison

**Rough idea**

- Run the same spec multiple times
- Vary:
  - model
  - temperature / settings
  - agent prompts
- Compare:
  - resulting artifacts
  - plans
  - file manifests

This is *not* traditional diffing. It’s semantic and structural.

**Open questions (intentionally unanswered)**

- What is the unit of comparison?
- Files? Plans? Decisions?
- How do you avoid Goodhart-style over-metrics?

This space should remain speculative for now.

### 4. Agent Roles as Replaceable Modules

#### 4.1 Agent Swappability

Future direction:

- Treat agents as interchangeable strategies
- Example:
  - different "Engineering Lead" personas
  - different testing philosophies

This enables:

- controlled experiments
- pedagogy
- stress-testing assumptions

But it also multiplies surface area. Deferred intentionally.

### 5. Non-Goals (For Now)

These are explicitly **out of scope** for the foreseeable future:

- Self-modifying agents
- Long-term memory across runs
- Autonomous project continuation
- "Fully automatic" software generation without human checkpoints

The system is meant to be *inspectable, interruptible, and educational* — not autonomous.

### 6. The Missing Thought (Likely Candidates)

Based on prior discussions, the thought you forgot may have been one of these:

- **Human-in-the-loop phase gates** as a first-class design element
- **Failure capture as a feature** (failed runs are artifacts, not waste)
- **Pedagogical mode**: making the system explain *why* decisions were made
- **Run journals**: narrative summaries stitched from artifacts

None of these need to be decided now.

### 7. Closing Note

This project has already crossed the threshold from *exercise* to *system*.
Future work should prioritize:

- clarity over cleverness
- containment over capability
- learning over automation

If it feels heavy: that’s a signal to stop — not to simplify prematurely.
