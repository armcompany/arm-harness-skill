# Failure Ratchet Playbook

Use this reference when an agent makes the same kind of mistake or when a team wants each observed failure to improve the harness.

## Ratchet Loop

1. Capture the failure as evidence.
2. Identify the missing assumption, guide, tool, sensor, or permission boundary.
3. Decide whether the fix should be feedforward, feedback, or both.
4. Implement the smallest control that would have changed the outcome.
5. Validate against the original failure.
6. Record why the control exists.
7. Revisit later and remove it if it becomes obsolete or noisy.

## Failure-to-Control Examples

| Observed failure | Feedforward control | Feedback sensor |
| --- | --- | --- |
| Agent commented out failing tests | AGENTS.md rule: never comment tests; fix or delete with explanation | pre-commit grep for `.skip`, `xit`, commented test blocks |
| Agent used wrong package manager | AGENTS.md rule with exact command | hook fails when lockfile mismatch appears |
| Agent changed forbidden legacy path | AGENTS.md protected-path rule | diff scanner blocks edits under protected path |
| Agent finished without running tests | completion checklist | finalization hook checks test command evidence |
| Agent overengineered a small fix | skill guidance: smallest coherent change | review agent asks whether simpler local change exists |
| Agent violated module boundary | architecture skill | dependency rule, ArchUnit, dep-cruiser, import linter |
| Agent generated plausible but unverified UI | browser-testing skill | Playwright screenshot and pixel/visibility checks |
| Agent missed fresh API changes | docs lookup rule | CI test against current API or schema |
| Agent ran destructive shell command | safe command policy | pre-tool hook denies command or requests approval |

## Choosing the Control

Use a deterministic sensor when:

- the violation is syntactic or structural
- the signal can be computed cheaply
- the team can tolerate occasional false positives
- the fix can be explained by the sensor output

Use an inferential sensor when:

- the issue requires semantic judgment
- the risk is high enough to justify cost
- deterministic checks would be brittle or incomplete
- a human would otherwise perform repetitive review

Use a guide when:

- the agent needs context before acting
- the preferred behavior depends on team conventions
- the cost of a feedback-only miss is high
- the issue cannot be detected reliably afterward

## Control Quality Checklist

- The control points to a specific behavior.
- The placement is close to where the failure happens.
- The control has an owner or maintenance path.
- The failure message tells the agent how to self-correct.
- The control avoids leaking secrets or expanding permissions.
- The control can be tested with a small fixture or replay.
- The control does not contradict another guide or sensor.

## Anti-Patterns

- Adding broad advice after every failure.
- Letting AGENTS.md grow into a full engineering handbook.
- Using LLM review for things a linter can catch.
- Adding a sensor that only tells humans, not the agent.
- Trusting AI-generated tests as the only behavior sensor.
- Installing many overlapping tools that confuse tool choice.
- Keeping obsolete mitigations after the model or platform improves.
- Treating a random bad run as a permanent rule without evidence or risk.
