---
name: harness-engineering
description: >-
  Design, audit, and improve coding-agent harnesses: the prompts, AGENTS.md/CLAUDE.md rules, skills, tools, MCP servers, hooks, CI checks, sandboxes, subagents, planning loops, memory/context policies, and feedback sensors around an AI coding model. Use when Codex is asked for harness engineering, engenharia de arnes, agent-harness design, coding-agent autonomy, reducing agent mistakes, turning repeated agent failures into rules or checks, creating AGENTS.md/CLAUDE.md guidance, designing hooks or CI sensors for agents, building a harness template for a stack, auditing an existing agent setup, or improving guide/sensor coverage for maintainability, architecture fitness, behavior, security, or runtime reliability.
---

# Harness Engineering

## Overview

Treat a coding agent as `model + harness`. Improve the harness by making desired behavior explicit, observable, and self-correcting through guides, sensors, execution controls, and ratcheted lessons from real failures.

## Operating Model

Use this skill to produce one of four outputs:

- **Harness audit**: inventory current guides, sensors, hooks, tools, and gaps.
- **Harness design**: propose a coherent target harness for a repo, team, stack, or agent workflow.
- **Harness implementation**: edit AGENTS.md, skills, scripts, hooks, CI, review prompts, or templates.
- **Harness ratchet**: convert observed agent failures into minimal durable controls.

Prefer small, enforceable controls over long rule documents. Every durable rule should trace to a real failure, external constraint, or high-risk workflow.

## Workflow

1. Clarify the bounded context: target agent(s), repository or service topology, autonomy level, failure history, CI/release constraints, and what "less supervision" should mean.
2. Inventory the current harness before proposing changes. If filesystem access is available, run:

   ```bash
   python skills/harness-engineering/scripts/audit_harness.py . --format markdown
   ```

   If the skill is installed elsewhere, resolve the script path from the skill directory.

3. Classify each control by direction, execution type, lifecycle position, and regulation category. Read `references/control-taxonomy.md` when designing the matrix.
4. Work backward from desired behavior or observed failures to harness components. Use `references/ratchet-playbook.md` for failure-to-control conversion.
5. Design the smallest coherent change set. Use `references/harness-blueprint.md` for component patterns and `references/templates.md` for concrete artifacts.
6. Implement controls where they naturally belong:

   - Put always-on, high-signal conventions in AGENTS.md/CLAUDE.md.
   - Put detailed or task-specific procedures in skills or references with progressive disclosure.
   - Put deterministic checks in hooks, scripts, CI, linters, tests, or structural analyzers.
   - Put semantic judgment in review skills, evaluator agents, or LLM-as-judge workflows.
   - Put safety and permissions in gates, sandboxes, allowlists, and approval policies.

7. Validate by simulating at least one previously observed failure. A harness improvement is not done until the new guide or sensor would have prevented, surfaced, or corrected the failure.

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
