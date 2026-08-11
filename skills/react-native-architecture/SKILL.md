---
name: react-native-architecture
description: >-
  Design, audit, and implement production React Native architectures for Expo or Bare projects: workflow choice, monolith or modular superapp topology, GraphQL or REST data layer, render/logic separation, hook design, TanStack Query and Zustand state boundaries, end-to-end typing with codegen and Zod, folder structure, unit/integration/E2E test strategy with Jest, Testing Library, MSW, Maestro or Detox, and management, CI, and release scripts. Use for React Native or Expo architecture reviews, greenfield app structure, arquitetura React Native, mobile refactors, module extraction, state management decisions, or turning an unstructured app into a verifiable one.
---

# React Native Architecture

## Overview

Treat a mobile app as `product surface + architecture contracts + verification`. This skill does not start from a folder template. It starts by interrogating the decisions that make a template correct, records them, then implements only what those decisions justify.

An architecture is finished when a rule is either enforced by a script, a type, a test, or a lint rule — or explicitly recorded as a judgment call with its cost.

## Operating Model

Produce one or more of five outputs:

- **Architecture interview**: force the unresolved decisions to the surface and record them.
- **Architecture audit**: inventory an existing app against the contracts in this skill and list violations with file paths.
- **Architecture design**: propose topology, data layer, state boundaries, typing pipeline, folder structure, and test/release lanes.
- **Architecture implementation**: create or refactor the structure, hooks, data layer, scripts, and gates.
- **Architecture ratchet**: turn one observed defect (crash, race, duplicated fetch, untyped payload, flaky E2E) into a durable contract.

Never answer "Expo or Bare", "REST or GraphQL", or "monolith or superapp" from preference. Answer from constraints. Read `references/architecture-interview.md` before proposing a topology.

## Workflow

1. Resolve the project root and read its agent instructions, `package.json`, `app.json`/`app.config.*`, and lockfile before changing anything.
2. Detect the current state. If filesystem access is available, run:

   ```bash
   python skills/react-native-architecture/scripts/audit_rn_project.py . --format markdown
   ```

   Treat its output as evidence, not as permission to run installs, builds, or codegen.

3. Run the architecture interview. Read `references/architecture-interview.md`. Ask only the questions whose answers change the deliverable; infer the rest from repository evidence and state the inference explicitly.
4. Record every decision as an ADR using the template in `references/templates.md`. A decision with no recorded alternative and cost is not a decision.
5. Choose the topology. Read `references/project-structure.md` for the monolith feature-first and modular superapp layouts, module contracts, and the extraction path between them.
6. Design the data layer. Read `references/data-layer.md` for the REST vs GraphQL decision, transport isolation, cache keys, offline/optimistic behavior, and error taxonomy.
7. Draw the state boundary. Read `references/state-and-hooks.md` for the TanStack Query vs Zustand split, hook layering rules, naming, and the render/logic separation contract.
8. Lock the type pipeline. Read `references/typing-contracts.md` for strict TypeScript settings, generated clients, Zod at the boundaries, and branded domain types.
9. Define verification. Read `references/testing-strategy.md` for the unit/integration/contract/E2E mix, what each layer is allowed to mock, and which gates block a merge or a release.
10. Wire the scripts. Read `references/scripts-and-release.md` for the canonical npm script set, CI lanes, EAS/Fastlane, OTA policy, and native-change detection.
11. Validate the result against the recorded decisions:

    ```bash
    python skills/react-native-architecture/scripts/validate_rn_architecture.py . --format markdown
    ```

12. Simulate one real failure the new architecture is supposed to prevent. If nothing fails when the contract is broken, the contract is decoration — replace it with a check.

## Decision Rules

- Default to **Expo with Continuous Native Generation**. Choose Bare only against a concrete blocker: an unsupported native dependency, a custom build pipeline, an existing brownfield native app, or a native team that owns the platform projects. Record the blocker.
- Default to **monolith, feature-first**. Choose a modular superapp only when at least two of these hold: independent teams owning independent domains, independent release or feature-flag lifecycles, host/mini-app runtime isolation, or an app that already exceeds the point where a single build graph is the bottleneck.
- Choose **GraphQL** when many screens compose overlapping entities from one graph and a schema owner exists. Choose **REST** when endpoints are stable, cacheable, owned by others, or the backend has no schema discipline. Never run both transports for the same domain without a stated migration deadline.
- **TanStack Query owns server state. Zustand owns client state.** Never mirror fetched data into a store to "share" it; share the query key instead.
- **Components render. Hooks decide. Modules fetch.** A component file that imports a transport client, a store creator, or a date/currency library directly is an architecture violation.
- **No untyped boundary.** Every network payload, deep link param, storage read, and native module response is validated or generated. `any` at a boundary is a defect, not a style issue.
- **A test tier may only mock the tier below it.** Unit tests mock nothing but time and randomness; integration tests mock transport, not hooks; E2E mocks nothing but backend environment selection.
- Native-affecting changes invalidate OTA. Detect them and force a build; never ship a native-dependency change over the air.
- Prefer deleting a layer to adding an abstraction that only forwards calls. One-line pass-through wrappers are cost without control.
- Do not introduce a library that duplicates an existing one already in the lockfile. Migrate or keep, never both.

## Anti-Patterns To Flag

- `useEffect` used to derive state that is computable during render, or to sync a store with a query.
- Screens that fetch and also format and also branch on loading/error inline with layout.
- A global store holding server entities, pagination cursors, or request status.
- `index.ts` barrel files that re-export whole features and destroy tree-shaking and module boundaries.
- Deep relative imports (`../../../features/x/internal/y`) crossing a feature or module boundary.
- Navigation params typed as `any` or as loose records.
- Snapshot tests standing in for behavior tests.
- E2E suites that assert on implementation-level test IDs generated by the render tree rather than on user-visible outcomes.
- `console.log` observability with no crash reporter, breadcrumb, or release-tagged source maps.

## Output Shapes

For an **architecture interview**, return: resolved decisions, open decisions with the evidence needed, and the ADR set to write.

For an **audit**, return: detected stack and versions, contract violations grouped by severity with `path:line`, missing sensors, and a prioritized fix order with the check that proves each fix.

For a **design**, return: topology diagram in text, folder tree, data-layer contract, state boundary table, type pipeline, test matrix with gates, script set, and release policy.

For an **implementation**, edit the project directly when asked, follow the existing conventions of that repository, and finish with typecheck, lint, and the relevant test lane actually run and reported.

## References

- Read `references/architecture-interview.md` to run the decision interview and score Expo/Bare, monolith/superapp, and REST/GraphQL.
- Read `references/project-structure.md` for monolith and modular superapp folder layouts, module contracts, boundary enforcement, and the extraction path.
- Read `references/state-and-hooks.md` for the server/client state boundary, hook layers, naming rules, and render/logic separation.
- Read `references/data-layer.md` for transport isolation, query key design, mutations, offline, retries, and error taxonomy.
- Read `references/typing-contracts.md` for strict TypeScript, codegen, Zod boundaries, navigation typing, and env typing.
- Read `references/testing-strategy.md` for the test pyramid, tier mocking rules, Maestro/Detox choice, fixtures, and CI gates.
- Read `references/scripts-and-release.md` for the canonical scripts, CI lanes, EAS/Fastlane, OTA policy, versioning, and observability.
- Read `references/templates.md` for ADR, module contract, hook, screen, query, store, and PR checklist templates.
