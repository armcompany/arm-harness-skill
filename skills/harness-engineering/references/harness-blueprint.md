# Harness Blueprint

Use this reference to design a concrete harness from desired behavior.

## Component Map

| Desired behavior | Harness component |
| --- | --- |
| Work on code and data larger than context | filesystem, git, progress files, artifact directories |
| Execute and verify code | shell, language runtimes, test runners, browser automation |
| Operate safely | sandbox, permission gates, command allow/deny lists, approval flows |
| Learn project-specific conventions | AGENTS.md, CLAUDE.md, skills, memory files |
| Access fresh knowledge | web search, docs MCPs, internal knowledge MCPs |
| Stay coherent in long tasks | planning files, compaction, tool-output offloading, handoff files |
| Avoid premature completion | completion criteria, verification hooks, continuation loops |
| Avoid self-serving evaluation | separate reviewer/evaluator agents, explicit acceptance criteria |
| Coordinate parallel work | subagents, worktrees, mailboxes, task boards, merge-conflict policy |
| Improve over time | failure log, harness backlog, recurring drift scans |

## AGENTS.md / CLAUDE.md

Use for always-on, high-value instructions:

- package manager and test commands
- local bootstrap rules
- critical architecture boundaries
- unsafe paths or commands
- conventions that are not discoverable from code
- verification required before final response

Keep it short. If a rule needs paragraphs, move it into a skill or reference and link to it.

Good rule:

```markdown
- Do not comment out failing tests. Fix them or delete them with an explanation.
```

Weak rule:

```markdown
- Be careful and write clean maintainable code.
```

## Skills and Progressive Disclosure

Use skills for procedures that are useful only for some tasks:

- how to add a new endpoint in this stack
- how to test a browser flow
- how to perform architecture review
- how to create a migration
- how to debug production-like logs

Keep the skill's main file procedural and concise. Put long examples, schemas, and detailed standards in references that are loaded only when needed.

## Tools and MCP Servers

Tool descriptions enter the model's trusted context. Keep tool menus small and non-overlapping.

Before adding a tool or MCP server, ask:

- What behavior does this enable that the agent cannot already perform?
- Is the tool description trustworthy and scoped?
- What data or permissions does it expose?
- Can a deterministic script replace an inferential workflow?
- How will failures be reported back to the agent?

## Hooks and Middleware

Use hooks to enforce things agents forget:

- block destructive commands
- run formatting after edits
- run type checks or fast tests after relevant file changes
- prevent commented-out tests or skipped tests
- require approval for publishing, pushing, or deleting data
- offload long tool outputs to files and return a short pointer

Principle: success is silent; failure is verbose and actionable.

## Sandboxes and Safe Defaults

Do not rely on the model to self-police risky operations. Design the execution environment:

- isolate filesystem and credentials
- default network access to off unless needed
- preinstall expected runtimes and CLIs
- require approval for irreversible actions
- keep logs, screenshots, and test outputs available as artifacts

## Long-Horizon Work

For tasks spanning multiple sessions or context windows:

- maintain a plan file with state, decisions, and completion criteria
- write a handoff file before compaction or restart
- store large outputs on disk and summarize only the relevant pointers
- separate planner, implementer, and evaluator roles when stakes justify it
- use worktrees or isolated branches for parallel agents

Do not use continuation loops without objective completion criteria. Otherwise the agent may keep working after the marginal value is gone.

## Observability

Instrument the harness itself:

- which sensors fired
- which checks were skipped
- which rules are frequently violated
- token and latency cost of each control
- failure classes that still escape to humans

Use this data to prune noisy controls and add missing ones.
