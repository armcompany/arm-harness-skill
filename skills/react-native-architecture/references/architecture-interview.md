# Architecture Interview

Run this before proposing structure. Skip any question the repository already answers, and say which evidence answered it. Stop asking once the remaining answers no longer change the deliverable.

## 1. Product and constraint frame

| Question | Why it changes the architecture |
| --- | --- |
| What must the app do offline? | Decides persistence, mutation queue, and whether the cache is authoritative. |
| Which platforms and minimum OS versions ship? | Decides native dependency freedom, New Architecture posture, and E2E device matrix. |
| Who owns the backend contract? | Decides GraphQL viability and codegen ownership. |
| How often do you ship, and can you ship a store binary that week? | Decides OTA policy and native-change discipline. |
| How many engineers, in how many teams, touch this app? | Decides monolith vs modular superapp more than code size does. |
| Are there regulated flows (payments, health, identity)? | Decides logging, storage, screenshot policy, and test evidence requirements. |
| Is there an existing native app to embed into or absorb? | Decides brownfield integration and forces Bare or a custom host. |

## 2. Expo vs Bare

Score against blockers, not taste. Default is **Expo with Continuous Native Generation** (`app.config.ts` + config plugins + prebuild when needed).

Choose **Bare** only if one of these is true and recorded:

- A required native dependency has no Expo config plugin and cannot get one at acceptable cost.
- The organization already owns and maintains the iOS/Android projects, with native CI and native reviewers.
- The app is brownfield: React Native is embedded into an existing native host.
- Build tooling must be custom in a way EAS cannot express (internal signing infrastructure, exotic build variants).

Notes that hold either way:

- Bare does not remove Expo modules. `expo-*` packages install into Bare projects; the choice is about who owns `ios/` and `android/`.
- Expo + config plugins covers most "we need native code" cases. Write a local config plugin before ejecting the whole project.
- Committing `ios/` and `android/` in a CNG project is a decision with a cost: prebuild output drifts and upgrades get manual. Record it if you do it.
- Verify current Expo SDK and React Native version compatibility in official docs before pinning. Do not assume a version pairing from memory.

## 3. Monolith vs modular superapp

Default: **monolith, feature-first**. It is faster, has one build graph, one dependency set, and one test lane.

Move to **modular** when at least two hold:

- Two or more teams own domains that change independently and block each other in review.
- Domains need independent enablement (feature flags, per-tenant availability, staged rollout per domain).
- The app hosts third-party or semi-independent mini-apps with a runtime contract.
- Build, typecheck, or test time on the single graph is a measured bottleneck, not a feeling.

Modular has three levels; pick the lowest that solves the problem:

1. **Enforced folders** — one package, boundaries enforced by lint rules (`import/no-restricted-paths`, ESLint boundaries). Zero infrastructure cost.
2. **Workspace packages** — pnpm/yarn workspaces + TypeScript project references. Real compile-time boundaries, shared design system as a package, per-package tests.
3. **Runtime host + mini-apps** — a host shell with a registration contract, isolated navigation subtrees, and per-module lifecycle. Only for genuine superapps; the cost is a whole platform team.

Never start at level 3. Level 1 to level 2 is a mechanical migration if the folder structure was feature-first from day one.

## 4. REST vs GraphQL

| Signal | Points to |
| --- | --- |
| One schema owner, screens compose overlapping entities, over-fetching hurts on mobile networks | GraphQL |
| Fragment colocation and generated hooks are a workflow the team will actually maintain | GraphQL |
| Endpoints owned by several backend teams with no unified schema | REST |
| Heavy file upload/download, streaming, or CDN-cacheable resources | REST |
| Backend has OpenAPI already and no appetite for a graph | REST |
| The team has never operated a GraphQL client cache in production | REST, or GraphQL through TanStack Query with a thin client |

Decision detail that matters more than the transport: **who caches**. Options:

- **TanStack Query + `fetch`/`ky`/`axios`** for REST. One cache, one mental model, works identically for GraphQL over POST via `graphql-request`.
- **Apollo Client** normalized cache for GraphQL when entity-level cache updates across screens are a real requirement.
- **urql + graphcache** as a lighter normalized option.

If you cannot articulate why you need a normalized cache, use TanStack Query. Document-level caching is enough for most apps and is far easier to debug.

Never run two data layers for the same domain without a written migration deadline and an owner.

## 5. Navigation

- **`expo-router`** (file-based, typed routes) is the default for new Expo apps: deep links, layouts, and typed params come from the file tree.
- **React Navigation directly** when routes are dynamic, driven by a remote manifest, or when a modular host registers subtrees at runtime.
- Either way, navigation params are typed and validated. See `references/typing-contracts.md`.

## 6. Remaining decisions to record

Ask or infer, then record each in an ADR:

- Styling: StyleSheet + tokens, Unistyles, Tamagui, or NativeWind — one, not two.
- Design system: in-app folder, workspace package, or external.
- Persistence: MMKV (fast key-value), SQLite/op-sqlite or Drizzle (relational), SecureStore/Keychain (secrets). Never AsyncStorage for tokens.
- Auth: token storage, refresh strategy, and what happens to the query cache on logout.
- i18n and RTL support: required now or explicitly deferred.
- Observability: crash reporter, breadcrumbs, release tagging, source map upload.
- Analytics: event schema owner and whether events are typed.
- Feature flags: provider, and whether flags gate navigation entries.
- Accessibility floor: labels, dynamic type, contrast, and whether it is tested.
- E2E runner: Maestro or Detox (see `references/testing-strategy.md`).
- Release: EAS Build/Submit or Fastlane; OTA update policy and rollback.

## 7. Output of the interview

Return three lists:

1. **Resolved** — decision, evidence or answer, and the ADR to write.
2. **Assumed** — decision made from inference, with the inference stated so it can be corrected cheaply.
3. **Blocked** — decisions that need a person: schema ownership, release cadence, regulated-data scope, team topology.

Do not begin implementation while a level-3 modular decision or the Expo/Bare decision is still blocked. Everything else can start under a stated assumption.
