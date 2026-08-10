# Persistent Project Harness

Use this pattern when an agent must continue a mission across threads, restarts, editors, providers, or models. The state belongs to the project, not to the model's memory.

## Core principles

1. Repository artifacts own operational state; code, Git diff, tests, and runtime behavior own technical truth.
2. Recovery is reconciliation, not blind trust in the last journal entry.
3. One logical task runs at a time. Every task declares its validation before implementation.
4. Written code is not proof. `DONE` requires the declared check to pass.
5. Record operational facts, decisions, and outcomes—never private chain-of-thought.
6. Keep the harness proportional. Omit files and automation that do not improve recovery or correctness.

## Recommended structure

```text
AGENTS.md
.harness/
  mission.md
  plan.md
  state.json
  journal.md
  errors.json
  decisions.md
  architecture.md
  context.md
  checkpoints/
```

Optionally add detailed procedures under `.agents/harness/`, specifications under `specs/`, architecture decisions under `docs/architecture/adr/`, and deterministic checks under `scripts/`. Adapt names to existing repository conventions rather than duplicating an established system.

## Artifact responsibilities

- `AGENTS.md`: short, always-on resume, execution, validation, safety, and stack-specific rules.
- `mission.md`: current product reality, objective, scope, definition of done, constraints, and exclusions.
- `plan.md`: milestone-sized tasks with IDs, dependencies, validation, and status.
- `state.json`: minimal operational cursor—current task, next action, blockers, completions, failures, checkpoint, and check results.
- `journal.md`: chronological factual execution log.
- `errors.json`: only durable, actionable failures and attempted remedies.
- `decisions.md`: non-trivial architectural or dependency decisions and their impact.
- `architecture.md`: architecture actually observed in the repository.
- `context.md`: high-value onboarding summary, not a second architecture document.
- `checkpoints/`: textual snapshots after relevant logical changes; never copies of source code.

## Resume and recovery

On a new session:

1. Read repository instructions, mission, state, plan, journal, architecture, and the checkpoint referenced by state.
2. Inspect the current code, relevant specs, Git status, and diff.
3. Check whether the current task, plan status, checkpoint, and actual implementation agree.
4. Repair stale harness records when the code provides stronger evidence.
5. State `CURRENT_STATE`, `CURRENT_OBJECTIVE`, `NEXT_ACTION`, and `BLOCKERS`.
6. Resume the smallest valid next action. Never repeat a completed task without regression evidence.

If a previous provider or browser session was interrupted, verify the observable result before claiming progress. Authentication expiry or missing external access leaves implementation work `RUNNING` or `BLOCKED`; it does not turn an unverified task into `DONE`.

## Bounded FOR-L loop

1. **Frame** — set goal, non-goals, acceptance criteria, checks, and one `RUNNING` task.
2. **Observe** — inspect relevant code, specifications, ADRs, Git state, and current behavior.
3. **Run** — make the smallest coherent in-scope change.
4. **Verify** — run task-specific checks, then the repository's aggregate verification when appropriate.
5. **Learn / Loop** — diagnose failures, record only reusable findings, change the hypothesis, and retry.
6. **Persist** — update state, plan, journal, errors if useful, checkpoint, and next action.

Do not retry the same failed action unchanged more than twice. Avoid autonomous loops with no iteration bound, new evidence, or escalation rule.

## Status semantics

- `PENDING`: known work whose dependencies are not satisfied.
- `READY`: dependencies satisfied and safe to start.
- `RUNNING`: the single current logical task.
- `BLOCKED`: missing access, authority, external dependency, or material decision prevents progress.
- `DONE`: implementation exists and its declared validation passed.
- `FAILED`: bounded attempts with changed hypotheses still produced an actionable failure for handoff.

Keep at most one `RUNNING` task. A completed-task entry must correspond to `DONE` in the plan; a failed-task entry must correspond to `FAILED`.

## Validation ladder

Discover commands from the repository; never assume a package manager or stack. Prefer the cheapest relevant signal first:

1. structural/schema validation of harness files;
2. task-specific static checks or unit tests;
3. repository-wide type, lint, test, and build checks;
4. runtime or visual validation for behavior and UI;
5. external integration validation when credentials and services are available.

Compilation does not prove visual quality, navigation reachability, localization completeness, or that a control has a working handler. Record those as separate checks.

## Checkpoints

Create a checkpoint only after a relevant change, interruption boundary, validation result, or handoff. Include:

- task and prior state;
- changes and files involved;
- validations and exact outcomes;
- unresolved issues;
- next action.

Use stable sortable names such as `YYYY-MM-DDTHHMMSSZ-task-id.md`. Keep only checkpoints that help recovery.

## Failure ratchet

Translate recurring failures into the lightest durable control:

- premature completion -> status invariant plus validator;
- clickable control without behavior -> interaction test or reachability audit;
- repeated manual formatting drift -> formatter or lint rule;
- provider interruption -> recovery reconciliation and checkpoint;
- stale plan/state -> cross-file consistency sensor;
- visual regression after passing TypeScript -> screenshot or browser/device review.

Do not generalize product-specific facts into a reusable skill. Preserve them as examples or fixtures.

## Safety and Git

The harness does not broaden user authorization. Never automate destructive filesystem or Git commands, database resets, force pushes, production deploys, submissions, or secret changes without explicit approval. Initial harness setup should not commit, push, or rewrite history unless requested.
