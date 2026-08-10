# Arm Harness Skill

`harness-engineering` gives coding agents a persistent, project-owned execution system. It can analyze an existing repository, create or improve its Harness, execute features through explicit validation, recover after interruption, and turn repeated failures into durable controls.

The skill is language-agnostic. It detects repository evidence and adapts to JavaScript/TypeScript, React Native/Expo, Python, Go, Rust, Java/Kotlin, .NET, Ruby, PHP, Swift, and mixed-stack monorepos without creating a different Harness for each language.

## What problem it solves

An LLM session is temporary. A development mission usually is not. Without external state, a new thread or provider may repeat completed work, lose blockers, trust stale summaries, or declare success after writing code without validating it.

This skill moves operational memory into the repository:

```text
project/
├── AGENTS.md
└── .harness/
    ├── mission.md
    ├── plan.md
    ├── state.json
    ├── journal.md
    ├── errors.json
    ├── decisions.md
    ├── architecture.md
    ├── context.md
    └── checkpoints/
```

The exact structure is adapted to the existing project. Files that add no recovery or correctness value should be omitted.

## Capabilities

- audits guides, skills, hooks, MCP configuration, CI, tests, and feedback sensors;
- detects languages, frameworks, package managers, workspaces, and declared commands;
- maps the real architecture before changing code;
- creates a mission and a milestone-sized, verifiable plan;
- executes one logical task at a time;
- records task state, blockers, failures, decisions, and checkpoints;
- validates implementation before marking it complete;
- resumes work across threads, restarts, editors, providers, and models;
- supports mixed-stack repositories with separate validation lanes;
- converts recurring agent mistakes into concise rules or deterministic checks;
- can suggest relevant optional skills for the current task without installing or requiring them.

## Installation

Install from GitHub using [skills.sh](https://skills.sh/docs):

```bash
npx skills add armcompany/arm-harness-skill --skill harness-engineering
```

Use the equivalent global or agent-specific option documented by skills.sh when needed. Restart or reload the coding agent if it does not discover newly installed skills immediately.

Confirm that `harness-engineering` appears in the agent's available skills before relying on explicit `$harness-engineering` invocation.

## Quick start

Open the existing project—not an empty replacement project—and ask:

```text
Use $harness-engineering.

Analyze this existing repository completely and configure a persistent,
project-owned Harness. Preserve its architecture, dependencies, conventions,
and existing behavior. Discover the real validation commands before creating
the mission and plan. Do not commit or push.
```

After setup, provide a feature with its desired outcome and constraints:

```text
Use $harness-engineering.

Add biometric authentication to the existing mobile application.
Preserve password login as fallback, support Android and iOS, and execute
until the feature's Definition of Done passes. Record external blockers rather
than claiming completion without device validation.
```

After an interruption, a new thread only needs:

```text
Use $harness-engineering. Resume Harness.
```

## How feature execution works

The skill follows a bounded cycle:

```text
Frame
  ↓
Observe
  ↓
Run
  ↓
Verify ── failed ──> Diagnose → change hypothesis → Verify again
  │
  passed
  ↓
Persist state → Checkpoint → Next action
```

### Frame

The agent defines the current objective, non-goals, acceptance criteria, dependencies, required validation, and one `RUNNING` task.

### Observe

It inspects the relevant code, specifications, architecture decisions, Git status and diff, current runtime behavior, and Harness records. Current code and observable behavior remain the technical source of truth.

### Run

It makes the smallest coherent change that satisfies the current task while preserving existing architecture and unrelated work.

### Verify

It runs task-specific checks followed by wider repository checks when appropriate. Code being written or compiled is not automatically proof of correct behavior.

### Learn and loop

On failure, it diagnoses the cause, changes the hypothesis, records only reusable errors, and validates again. It does not repeat the same failed action unchanged indefinitely.

### Persist

After relevant outcomes, it updates the task plan, operational state, journal, errors when useful, checkpoint, and precise next action.

## Task statuses

| Status | Meaning |
| --- | --- |
| `PENDING` | A dependency or prior decision is outstanding. |
| `READY` | Dependencies are satisfied and the task can start. |
| `RUNNING` | The single logical task currently being executed. |
| `BLOCKED` | Access, authority, external dependency, hardware, or a material decision is missing. |
| `DONE` | The implementation exists and its declared validation passed. |
| `FAILED` | Bounded attempts with changed hypotheses still produced an actionable handoff failure. |

The Harness should never use `DONE` merely because code was written. It should never convert an unavailable or blocked validation into a passing result.

## Language and stack discovery

The same Harness adapts to the repository. Its inventory script detects evidence such as manifests, lockfiles, source files, package dependencies, and CI configuration.

```bash
python path/to/harness-engineering/scripts/audit_harness.py . --format markdown
```

Examples of validation lanes it can discover and confirm:

| Project evidence | Possible validation after confirmation |
| --- | --- |
| `package.json`, `tsconfig.json` | repository scripts, TypeScript, configured lint/tests/build |
| Expo dependency | TypeScript, tests, Expo Doctor, web/device/runtime checks |
| `pyproject.toml` | configured Ruff, mypy/Pyright, pytest, package build |
| `go.mod` | formatting, vet, tests, build |
| `Cargo.toml` | formatting, Clippy, tests, build |
| Gradle or Maven files | wrapper checks, static analysis, tests, assembly |
| `.sln` or project files | .NET formatting when configured, build, tests |
| `Gemfile` | configured RuboCop and RSpec/Minitest tasks |
| `composer.json` | Composer scripts, configured analysis and tests |
| `Package.swift` | configured lint/format, Swift tests, platform build |

These are candidates, not blindly executed defaults. Repository scripts, wrappers, CI commands, exact versions, and existing configuration take priority.

For monorepos, the Harness maps each workspace or service to its own commands and uses meaningful validation keys such as `frontend`, `api`, `mobile`, and `contracts`.

## What “execute until the end” means

The agent can normally continue autonomously through implementation, static analysis, tests, local builds, and available runtime checks. Completion is bounded by the feature's Definition of Done and the authority granted by the user.

Some outcomes require external conditions:

- device or simulator availability;
- browser access for visual validation;
- credentials or authenticated sessions;
- third-party services and test environments;
- product, legal, security, or architecture decisions;
- permission for deployment, publication, database changes, or destructive actions.

When one of these is missing, the correct result is `BLOCKED` with an exact recovery point—not a false success. Once the condition is resolved, `Resume Harness` continues from that point.

## Recovery behavior

On resume, the agent should:

1. read repository instructions and Harness state;
2. load the mission, plan, journal, architecture, and referenced checkpoint;
3. inspect current code and Git diff;
4. reconcile stale or inconsistent records;
5. state `CURRENT_STATE`, `CURRENT_OBJECTIVE`, `NEXT_ACTION`, and `BLOCKERS`;
6. continue the smallest valid next action;
7. avoid repeating completed work unless evidence shows a regression.

The journal is a handoff aid, not technical truth. Code, tests, Git state, runtime behavior, and external systems must be checked again when relevant.

## Optional skill recommendations

The Harness may recommend skills based on the task and available catalog. Recommendations are contextual and optional; they do not install dependencies or change architecture.

Examples:

- `ponytail` for minimal, dependency-conscious implementation;
- `frontend-design` for intentional interface construction;
- `ui-ux-pro-max` for detailed UX, responsive, and accessibility work;
- `grill-me` for requirement pressure-testing before risky work;
- `caveman` for context-efficient long sessions;
- Redux-related skills only when the repository actually uses that architecture.

If a suggested skill is absent, the Harness should continue with its core workflow unless that capability is truly required.

## Useful prompts

### Create or upgrade a Harness

```text
Use $harness-engineering to audit this existing repository and create or
improve a persistent Harness. Preserve current conventions, discover every
stack and validation lane, and leave a verified next action for another agent.
```

### Execute a feature

```text
Use $harness-engineering. Add the following feature and execute one verified
task at a time until its Definition of Done passes:

[feature]
[acceptance criteria]
[constraints]
```

### Resume

```text
Use $harness-engineering. Resume Harness.
```

### Audit without changing code

```text
Use $harness-engineering to audit this repository's agent guides, persistent
state, tools, hooks, CI checks, permissions, and feedback sensors. Report gaps
and prioritized improvements without implementing them.
```

### Ratchet a repeated failure

```text
Use $harness-engineering. This agent failure has happened repeatedly:
[failure evidence]

Add the smallest durable guide or sensor that prevents, detects, or corrects it,
then simulate the failure to verify the control.
```

### Validate Harness consistency

```text
Use $harness-engineering to reconcile and validate the existing .harness state
against the current plan, checkpoint, code, and Git diff.
```

The bundled structural validator can also be run directly:

```bash
python path/to/harness-engineering/scripts/validate_project_harness.py .
```

## Safety boundaries

The Harness does not broaden the user's authorization. It should not automatically:

- delete broad filesystem paths or reset databases;
- rewrite Git history, force-push, commit, or push without authorization;
- deploy or publish to production;
- run production mobile submissions or over-the-air releases;
- expose or change secrets and environment files unnecessarily;
- install tools or replace frameworks merely by preference.

The agent should resolve exact targets, preserve unrelated work, and request authority when a required action has material external impact.

## Included resources

- `SKILL.md`: core workflow and routing instructions;
- `references/persistent-project-harness.md`: persistent state and recovery model;
- `references/project-harness-templates.md`: adaptable artifact templates;
- `references/stack-discovery.md`: stack detection and validation guidance;
- `references/security-production.md`: trust, MCP, secrets, supply-chain, deployment, migration, and production gates;
- `references/control-taxonomy.md`: guide and sensor classification;
- `references/harness-blueprint.md`: component design patterns;
- `references/ratchet-playbook.md`: failure-to-control process;
- `references/sdd-pattern.md`: specification-driven behavior workflow;
- `scripts/audit_harness.py`: conservative repository inventory;
- `scripts/test_audit_harness.py`: dependency-free multi-stack detection checks;
- `scripts/validate_project_harness.py`: cross-file state validator and failure simulation.

The skill intentionally does not include a project scaffold, framework replacement, or universal test command. It extends the project that already exists.
