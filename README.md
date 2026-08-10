# Arm Harness Skill

Reusable coding-agent harness engineering for persistent, verifiable work across threads, restarts, editors, providers, and models.

The skill can audit an existing agent setup, create a project-owned Harness, resume an interrupted mission, and turn recurring agent failures into durable guides or deterministic checks.

## Install with skills.sh

```bash
npx skills add armcompany/arm-harness-skill --skill harness-engineering
```

See the [skills.sh documentation](https://skills.sh/docs) for supported agents and installation options.

## Use

Invoke the skill explicitly when creating the Harness:

```text
Use $harness-engineering to analyze this repository and create a persistent,
project-owned Harness. Preserve the existing architecture and discover the
project's real validation commands before writing the mission and plan.
```

Later, a new thread or agent can continue with:

```text
Use $harness-engineering. Resume Harness.
```

The resume flow reads project state, reconciles it with the current code and Git diff, identifies the next valid action, executes one bounded task, validates it, and persists a checkpoint.

Other useful requests:

```text
Use $harness-engineering to audit this repository's guides and sensors.
Use $harness-engineering to turn this repeated agent failure into a durable control.
Use $harness-engineering to validate the consistency of the existing .harness state.
```

## Included

- persistent mission, plan, state, journal, error, decision, architecture, context, and checkpoint pattern;
- bounded `Frame -> Observe -> Run -> Verify -> Learn/Loop -> Persist` protocol;
- clear `DONE`, `BLOCKED`, and `FAILED` semantics;
- repository inventory script;
- deterministic project Harness validator with failure simulation;
- templates and guidance for recovery, validation, safety, and failure ratcheting.

The skill adapts the Harness to the target repository. It does not impose the ArmChar application's architecture, package manager, or product rules on other projects.
