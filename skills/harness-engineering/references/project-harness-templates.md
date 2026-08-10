# Project Harness Templates

Adapt these templates to facts discovered in the repository. Do not fill gaps with invented product, architecture, commands, or validation results.

## `state.json`

```json
{
  "mission": "Concise current mission",
  "status": "running",
  "currentTask": "H-001",
  "nextAction": "Specific executable next action",
  "blockers": [],
  "completedTasks": [],
  "failedTasks": [],
  "lastCheckpoint": null,
  "updatedAt": "2026-01-01T00:00:00Z",
  "validation": {
    "harness": null,
    "typecheck": null,
    "lint": null,
    "tests": null,
    "runtime": null
  }
}
```

Validation keys should match the project. Values may be `null` or small objects containing status, command, timestamp, and useful evidence.

## `mission.md`

```markdown
# Mission

## Current Product State
## Main Objective
## Scope
## Definition of Done
## Constraints
## Out of Scope
```

## `plan.md`

```markdown
# Plan

## H-001 — Verifiable task description

- Dependencies: none
- Validation: exact observable check
- Status: READY
```

Prefer milestones and verifiable tasks over a giant low-level backlog.

## `journal.md`

```markdown
## 2026-01-01T00:00:00Z

Task: H-001
Action: Factual summary of work performed
Files changed: paths or none
Validation: command/check and result
Result: outcome
Next action: specific continuation
```

## `errors.json`

```json
{
  "errors": [
    {
      "id": "ERR-001",
      "timestamp": "2026-01-01T00:00:00Z",
      "task": "H-001",
      "error": "Actionable failure",
      "probableCause": "Evidence-backed hypothesis",
      "attemptedFixes": [],
      "status": "open",
      "resolution": null
    }
  ]
}
```

Skip transient noise that will not help a future agent.

## `decisions.md`

```markdown
# Decisions

## DEC-001 — Decision title

Context:
Decision:
Reason:
Alternatives:
Impact:
```

## `architecture.md`

Document only observed structure, entry points, navigation or routing, state management, services/APIs, authentication, persistence, tests, build tooling, and primary flows that actually exist.

## `context.md`

Summarize product purpose, current stage, architecture, constraints, current work, known problems, and where authoritative details live. Optimize for rapid recovery, not completeness.

## Checkpoint

```markdown
# Checkpoint — H-001

Timestamp:
Task:
State before:
Changes:
Files involved:
Validation:
Result:
Open issues:
Next action:
```

## Compact `AGENTS.md` policy

Include:

1. exact resume read order;
2. reconciliation with code and Git state;
3. required current-state declaration;
4. one-task bounded execution loop;
5. `DONE`, `BLOCKED`, and `FAILED` semantics;
6. project-specific commands and stack constraints discovered from source;
7. checkpoint and state update rules;
8. safety, secrets, deployment, and Git restrictions;
9. pointers to detailed procedures instead of duplicating them.
