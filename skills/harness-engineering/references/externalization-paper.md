# Externalization Paper Notes

Source: `doc/2604.08224v1.pdf`

Paper: Chenyu Zhou et al., "Externalization in LLM Agents: A Unified Review of Memory, Skills, Protocols and Harness Engineering", arXiv:2604.08224v1, April 2026.

Use this reference when a harness-engineering task needs academic framing, literature-grounded terminology, or a broader model that connects memory, skills, protocols, and harnesses.

## Core Thesis

The paper frames modern LLM-agent progress as a shift from relying on model weights to externalizing cognitive burdens into runtime infrastructure. The model remains important, but reliable agency increasingly comes from changing the task representation around the model.

The central organizing model:

- Memory externalizes state across time.
- Skills externalize procedural expertise.
- Protocols externalize interaction structure.
- The harness coordinates those externalized modules into governed execution.

This complements the practical harness-engineering rule: design from the behavior the model cannot reliably provide alone, then externalize that burden into a guide, sensor, protocol, memory, tool, or control loop.

## Cognitive Artifact Lens

The paper uses cognitive artifacts as the analogy: a useful artifact does not merely make an agent "stronger"; it changes the task into a form the agent can solve more reliably.

Practical translation:

- Memory changes recall into retrieval and recognition.
- Skills change improvisation into composition from reusable procedures.
- Protocols change ambiguous interaction into structured contracts.
- Harnesses change open-ended action into governed, observable workflows.

Use this framing when explaining why a harness is not just "more prompt" or "more tooling"; it is a representational redesign of the agent's work.

## Historical Progression

The paper describes a progression:

1. Capability in weights: knowledge and behavior are expected to be latent in the model.
2. Capability in context: prompts, retrieved documents, and examples steer the model at runtime.
3. Capability through infrastructure: memory, skills, protocols, tools, sandboxes, evaluators, and control logic become part of the agent system.

Harness engineering belongs to the third stage. It treats the runtime environment as a first-class artifact, not as incidental scaffolding.

## Memory Externalization

Memory handles the temporal burden of agency. It stores and retrieves project state, user preferences, execution traces, resolved ambiguities, prior failures, and reusable experience.

Design implications:

- Separate short-lived working context from long-lived memory.
- Treat memory as managed state, not a dumping ground.
- Govern read/write permissions, freshness, conflicts, and retrieval scope.
- Feed execution traces and repeated failures back into memory so they can become skills or rules.
- Avoid both over-abstracted memory that loses operational detail and under-abstracted memory that floods context.

For coding-agent harnesses, practical memory artifacts include progress files, handoff files, failure logs, architecture decision records, project rules, and test/debug traces.

## Skill Externalization

Skills handle the procedural burden of agency. They package operating procedures, decision heuristics, and normative constraints so agents do not rederive workflows every time.

Design implications:

- A skill is useful only if it can be discovered, selected, loaded, bound to tools, executed, and updated from feedback.
- Progressive disclosure is central: keep the main instruction lean and load detailed references only when needed.
- Skill descriptions are operational text, not passive documentation; they shape selection and trust.
- Skill evolution should be evidence-driven: execution traces, failure patterns, and user corrections justify revisions.
- A skill safe in a sandbox may need additional permissions or gates in production.

For this skill package, `SKILL.md` is the selection and workflow layer, while `references/` holds the larger procedural and conceptual material.

## Protocol Externalization

Protocols handle the interaction burden of agency. They define how agents discover capabilities, call tools, delegate work, stream state, enforce schemas, and exchange results.

Design implications:

- Protocols convert free-form intent into validated, inspectable calls.
- Tool schemas and MCP descriptions are part of the trusted harness surface.
- Agent-agent protocols make delegation and coordination auditable.
- Agent-user protocols define how intent is captured, normalized, clarified, and approved.
- Domain protocols encode workflow-specific governance such as identity, payment, compliance, or data boundaries.

For coding agents, protocols include MCP, structured tool schemas, review handoff formats, PR templates, issue contracts, CI status APIs, and subagent communication formats.

## Harness as Unification Layer

The paper treats the harness as the designed cognitive environment where memory, skills, and protocols become jointly effective.

Recurring analytical dimensions:

- Agent loop and control flow.
- Sandboxing and execution isolation.
- Human oversight and approval gates.
- Observability and structured feedback.
- Configuration, permissions, and policy encoding.
- Context budget management.

These map directly to practical harness engineering:

- Agent loop: planning, tool use, verification, termination criteria.
- Sandboxing: filesystem, network, credentials, runtime isolation.
- Oversight: approval gates for destructive, expensive, or externally visible actions.
- Observability: logs, traces, screenshots, sensor output, failure capture.
- Policy: AGENTS.md, hooks, permissions, MCP allowlists, org rules.
- Context: compaction, tool-output offloading, skill loading, handoffs.

## Module Interactions

The paper emphasizes that memory, skills, and protocols reinforce one another:

- Memory supplies evidence for skill formation.
- Skills structure what should be remembered after execution.
- Protocols make skills portable by giving them stable invocation surfaces.
- Memory can route protocol and tool choices based on prior outcomes.
- Protocol outputs become memory only after the harness normalizes and stores them.
- Context limits force the harness to decide which memories, skills, and protocol details enter the model boundary.

Use this when designing nontrivial harnesses: do not optimize one module in isolation if it increases friction or noise in the others.

## Parametric vs Externalized Capability

The paper frames a design tradeoff between what should live inside the model and what should remain external.

Externalize when the burden benefits from:

- persistence across sessions
- freshness and updatability
- reuse across tasks or agents
- auditability and rollback
- explicit governance
- deterministic validation
- cross-model portability

Keep behavior mostly parametric when:

- the task is cheap, one-off, and low-risk
- the control would add more overhead than value
- the model already handles the behavior reliably
- the artifact would be stale or hard to govern

This supports the principle of minimal sufficient externalization: add only the harness components that reduce real burden or risk.

## Self-Evolving Harnesses

The paper identifies self-evolving harnesses as an emerging direction: the harness can inspect execution failures, revise skills, update memory policies, adjust orchestration, or propose new controls.

Practical stance:

- Let agents propose harness changes, but gate durable changes through review.
- Keep harness configuration, policies, and skill revisions versioned.
- Evaluate changes against prior failures and regression cases.
- Prune redundant controls as models and tools improve.

This is the academic counterpart to the ratchet loop in `ratchet-playbook.md`.

## Costs, Risks, and Governance

Externalization is not automatically good. It expands the attack surface and can add cognitive overhead.

Risks to consider:

- Memory poisoning or stale memory.
- Skill injection or misleading skill descriptions.
- Protocol misuse, schema drift, or unsafe tool exposure.
- Conflicting guides and sensors.
- Excessive context overhead.
- Self-evolving harness drift.
- Shared-infrastructure versioning and trust problems.

Governance should be co-designed with the harness:

- mandatory review gates for critical updates
- versioning and rollback for memory, skills, and policies
- permission boundaries for tools and MCPs
- provenance and audit trails for externalized artifacts
- evaluation of whether controls are utility-positive

## Evaluation Dimensions

The paper argues that model-centric benchmarks under-measure the role of externalized infrastructure.

Evaluate harnesses with:

- Ablation: remove one harness component and measure degradation.
- Cross-model transfer: hold the harness constant while changing models.
- Cross-task transfer: reuse the harness on related tasks.
- Cost accounting: measure overhead versus reliability gain.
- Governance quality: inspectability, reversibility, permission control.
- Failure escape rate: which issues still reach humans.
- Sensor usefulness: whether failures are actionable for agent self-correction.

These dimensions can be added to harness audit reports when the user asks for rigorous evaluation.
