---
name: harness-engineering
description: >-
  Design, audit, implement, and resume coding-agent harnesses: AGENTS.md/CLAUDE.md rules, project-owned mission and state, plans, journals, checkpoints, recovery, skills, tools, MCP servers, hooks, CI checks, sandboxes, subagents, and feedback sensors. Use for harness engineering, engenharia de arnes, agent autonomy, persistent execution across threads or models, "Resume Harness", reducing repeated mistakes, turning failures into rules or checks, or building and auditing agent workflows.
---

# Harness Engineering

## Overview

Treat a coding agent as `model + harness`. Improve the harness by making desired behavior explicit, observable, and self-correcting through guides, sensors, execution controls, and ratcheted lessons from real failures.

## Operating Model

Use this skill to produce one or more of five outputs:

- **Harness audit**: inventory current guides, sensors, hooks, tools, and gaps.
- **Harness design**: propose a coherent target harness for a repo, team, stack, or agent workflow.
- **Harness implementation**: edit AGENTS.md, skills, scripts, hooks, CI, review prompts, or templates.
- **Harness ratchet**: convert observed agent failures into minimal durable controls.
- **Persistent project harness**: make mission state recoverable from repository artifacts instead of model memory.

Prefer small, enforceable controls over long rule documents. Every durable rule should trace to a real failure, external constraint, or high-risk workflow.

## Workflow

1. Resolve the repository root and read its agent instructions before changing anything.
2. Clarify the bounded context: target agents, topology, autonomy, failure history, checks, release constraints, and what "less supervision" means.
3. Inventory the current harness and detect its stacks before proposing changes. If filesystem access is available, run:

   ```bash
   python skills/harness-engineering/scripts/audit_harness.py . --format markdown
   ```

   If the skill is installed elsewhere, resolve the script path from the skill directory.

   Read `references/stack-discovery.md` for every detected stack. Prefer commands declared by the repository; treat conventional commands only as candidates until configuration confirms them.

4. If the request says **Resume Harness** or project state already exists, follow the recovery protocol in `references/persistent-project-harness.md` before selecting work.
5. Classify each control by direction, execution type, lifecycle position, and regulation category. Read `references/control-taxonomy.md` when designing the matrix.
6. Work backward from desired behavior or observed failures to harness components. Use `references/ratchet-playbook.md` for failure-to-control conversion.
7. Design the smallest coherent change set. For persistent execution, read `references/persistent-project-harness.md` and `references/project-harness-templates.md`; otherwise use `references/harness-blueprint.md` and `references/templates.md`.
8. Implement controls where they naturally belong:

   - Put always-on, high-signal conventions in AGENTS.md/CLAUDE.md.
   - Put detailed or task-specific procedures in skills or references with progressive disclosure.
   - Put deterministic checks in hooks, scripts, CI, linters, tests, or structural analyzers.
   - Put semantic judgment in review skills, evaluator agents, or LLM-as-judge workflows.
   - Put safety and permissions in gates, sandboxes, allowlists, and approval policies.

   For MCP, untrusted content, credentials, deployment, migrations, or production access, read `references/security-production.md` before proposing or executing controls. Its application security baseline (server-side authorization, secret hygiene, database exposure, RLS, authentication checks) applies to every piece of software created under the Harness, and its agent execution risk rules apply to the Harness's own operation.

9. Validate the changed artifacts and the target project's own checks. When a project harness exists, run `scripts/validate_project_harness.py <repo>`.
10. Simulate at least one relevant failure. A harness improvement is not done until the guide or sensor prevents, surfaces, or corrects it.

## Persistent Execution Protocol

Use a bounded `Frame -> Observe -> Run -> Verify -> Learn/Loop -> Persist` cycle. Work on one logical task at a time. The current code, Git diff, and runtime behavior remain the technical source of truth; harness records can be stale.

Each phase carries a built-in execution discipline:

- **Frame — scope gate.** Before declaring a task `RUNNING`, classify the request (spike, bounded change, or architectural work), align scope and acceptance criteria with the user, and get explicit approval of the intended approach. The ceremony scales with the task—two sentences in chat for a bounded change, a written spec for architectural work—but the approval gate never does. Never implement on assumptions the user has not confirmed.
- **Run — test first.** Where the repository has a test harness, write or extend a failing test that names the expected behavior, watch it fail for the right reason, implement the smallest change that passes it, then refactor. Where no test harness exists, declare the manual or scripted check that will stand in for one before writing code.
- **Verify — evidence before completion.** Mark a task `DONE` only after running its declared validation and observing the real output. Quote the evidence in the journal or checkpoint; never infer success from "code was written" or "it compiled".
- **Learn/Loop — systematic debugging.** On failure, reproduce reliably, form one root-cause hypothesis, change one variable, and re-verify. Investigate before fixing; a fix without a diagnosed cause is a guess. Record only durable, reusable findings.

On resume: load instructions, state, plan, journal, architecture, and the latest checkpoint; inspect current code and Git state; reconcile inconsistencies; then state `CURRENT_STATE`, `CURRENT_OBJECTIVE`, `NEXT_ACTION`, and `BLOCKERS`.

Mark work `DONE` only after its declared validation passes, with the command output as evidence. Use `BLOCKED` only for missing access, authority, an external dependency, or a material user decision. Use `FAILED` after bounded attempts with changed hypotheses leave an actionable failure. Do not retry an unchanged failed action indefinitely.

## Control Design Rules

- Favor feedback sensors when the issue is objectively checkable.
- Favor feedforward guides when the issue is contextual, semantic, or not cheaply checkable.
- Pair important guides with sensors; a rule with no observation loop quietly rots.
- Keep AGENTS.md/CLAUDE.md short. Treat it like a pilot checklist, not a style guide.
- Make success silent and failures verbose. Pass actionable error text back into the agent loop.
- Put fast deterministic sensors before commit; put expensive inferential or broad checks in PR or CI.
- Remove obsolete controls when models, tools, or codebase structure make them redundant.
- Do not add vague principles such as "write clean code" unless they are backed by concrete examples or checks.
- Do not install or recommend MCP servers, hooks, or scripts without considering prompt-injection and permission risks.
- Keep operational state concise and machine-readable. Journal and checkpoints record facts, not hidden reasoning.
- Do not repeat completed work without evidence of regression, and never trust the journal over the current repository.
- Create only artifacts that carry useful state; empty ceremony weakens the harness.

## Output Shapes

For a harness audit, return:

- Current harness inventory
- Control matrix
- Top risks and missing sensors
- Prioritized improvements with owner, placement, and validation method

For a harness design, return:

- Target behaviors
- Proposed guides and sensors
- Lifecycle placement
- Context and memory policy
- Safety/permission model
- Evaluation plan

For implementation, edit the project directly when asked. Keep changes scoped, follow existing repo patterns, and verify with the relevant checks.

## References

- Read `references/control-taxonomy.md` to classify guides, sensors, execution types, and regulation categories.
- Read `references/harness-blueprint.md` to design components such as AGENTS.md, hooks, tools, sandboxes, subagents, context compaction, and long-horizon loops.
- Read `references/ratchet-playbook.md` to convert agent failures into durable harness improvements.
- Read `references/templates.md` when drafting AGENTS.md, audit reports, control matrices, sprint contracts, or hook policies.
- Read `references/externalization-paper.md` when the task needs academic framing, literature-grounded language, or the memory/skills/protocols/harness externalization model.
- Read `references/sdd-pattern.md` when designing a specification-driven development flow, behavior harness, approved fixtures pattern, or spec-to-plan-to-tasks agent workflow.
- Read `references/persistent-project-harness.md` for project-owned state, recovery, task status, checkpoints, validation, and safety rules.
- Read `references/project-harness-templates.md` when creating the concrete persistent harness artifacts.
- Read `references/stack-discovery.md` to map languages, frameworks, package managers, and repository evidence to proportionate validation commands.
- Read `references/security-production.md` for trust boundaries, MCP/tool governance, secrets, supply-chain checks, release gates, migrations, rollback, and production authorization.
