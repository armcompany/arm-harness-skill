# Harness Engineering Templates

Use these templates as starting points. Adapt them to the repository and delete sections that do not apply.

## Harness Audit Report

```markdown
# Harness Audit

## Current Inventory

- Guides:
- Computational sensors:
- Inferential sensors:
- Tools and MCP:
- Hooks and permission gates:
- Context, memory, and handoff:
- CI and lifecycle placement:

## Control Matrix

| Control | Direction | Type | Category | Lifecycle | Owner | Notes |
| --- | --- | --- | --- | --- | --- | --- |

## Top Gaps

1. 
2. 
3. 

## Recommended Changes

| Priority | Change | Why | Files/tools | Validation |
| --- | --- | --- | --- | --- |

## Residual Risk

- 
```

## Compact AGENTS.md

```markdown
# Agent Instructions

- Use <package-manager> for all dependency and script commands.
- Run <fast-check-command> before finalizing code changes.
- Do not comment out or skip failing tests. Fix them or explain deletion.
- Do not edit <protected-path> unless the user explicitly asks.
- Follow <architecture-boundary> when adding imports or modules.
- Prefer the smallest scoped change that satisfies the request.
- If a command fails, report the exact command and relevant error before changing approach.
```

Keep this under roughly 60 lines. Move detailed workflows into skills or docs.

## Control Matrix

```markdown
| Desired behavior | Current control | Gap | Proposed guide | Proposed sensor | Lifecycle |
| --- | --- | --- | --- | --- | --- |
| Agent uses the right package manager | package-lock present | No explicit rule | AGENTS.md command rule | lockfile mismatch hook | pre-commit |
```

## Sprint Contract

Use before multi-step autonomous coding work.

```markdown
# Sprint Contract

## Goal

## Non-goals

## Files likely in scope

## Acceptance criteria

- 

## Required verification

- 

## Stop conditions

- Ask for help if:
- Do not proceed if:
```

## Hook Policy

```markdown
# Hook Policy

## Block

- destructive filesystem commands outside the workspace
- force pushes without explicit approval
- database destructive statements against non-local targets
- commits with secrets or credentials

## Warn and return actionable output

- failed type checks
- failed fast tests
- skipped or commented tests
- forbidden imports or module boundaries

## Silent on success

- formatting
- fast lint checks
- generated artifact refresh
```

## Failure Log

```markdown
# Agent Failure Log

| Date | Failure | Root cause | Harness change | Validation | Revisit |
| --- | --- | --- | --- | --- | --- |
```
