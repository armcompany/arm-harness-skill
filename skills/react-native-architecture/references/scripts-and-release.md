# Scripts, CI, and Release

Scripts are the architecture's sensors. A rule with no script behind it is advice.

## Canonical script set

```jsonc
{
  "scripts": {
    "start": "expo start",
    "android": "expo run:android",
    "ios": "expo run:ios",

    "typecheck": "tsc --noEmit",
    "lint": "eslint . --max-warnings=0",
    "format": "prettier --write .",
    "codegen": "graphql-codegen --config codegen.ts",
    "codegen:check": "pnpm codegen && git diff --exit-code src/core/api/generated",

    "test": "jest",
    "test:watch": "jest --watch",
    "test:ci": "jest --ci --coverage --maxWorkers=50%",
    "e2e:build": "eas build --profile preview --platform ios --local",
    "e2e:ios": "maestro test e2e/flows --include-tags=critical",
    "e2e:android": "maestro test e2e/flows --include-tags=critical",

    "doctor": "npx expo-doctor",
    "arch:audit": "python scripts/audit_rn_project.py . --format markdown",
    "arch:check": "python scripts/validate_rn_architecture.py . --strict",

    "verify": "pnpm typecheck && pnpm lint && pnpm codegen:check && pnpm test:ci && pnpm arch:check",

    "build:preview": "eas build --profile preview",
    "build:prod": "eas build --profile production",
    "submit:prod": "eas submit --profile production",
    "ota:staging": "eas update --branch staging",
    "ota:prod": "eas update --branch production"
  }
}
```

`verify` is the contract: one command an agent or a human runs before claiming done. Keep it fast enough that people actually run it (target under ~3 minutes locally); push slower checks to CI lanes.

Adapt names to the package manager and the existing repo. Do not rename a team's existing scripts to match this list — map to them.

## CI lanes

| Lane | Trigger | Steps | Typical budget |
| --- | --- | --- | --- |
| `quality` | every PR | install (cached), `typecheck`, `lint`, `codegen:check`, `arch:check` | < 5 min |
| `test` | every PR | `test:ci`, upload coverage | < 8 min |
| `build-preview` | PR touching native deps, config plugins, or `app.config.*` | `expo prebuild --clean` diff, EAS preview build | on demand |
| `e2e` | nightly + release branch | build preview artifact, run Maestro on iOS + Android | < 30 min |
| `release` | tag | production build, submit, source map upload, changelog | — |

Cache the package manager store and the Metro/Jest caches keyed by lockfile hash. Cold installs dominate mobile CI time.

## Native change detection

An OTA update can never ship a native change. Detect it mechanically:

```bash
# fails the PR if native surface changed without a build
git diff --name-only origin/main... | grep -E \
  '(package\.json|pnpm-lock\.yaml|app\.config\.(ts|js)|app\.json|ios/|android/|plugins/)' \
  && echo "native-affecting change: build required" && exit 1 || exit 0
```

Native-affecting changes include: any dependency with native code added/removed/upgraded, Expo SDK bumps, config plugin edits, permission or entitlement changes, app icon/splash native config, and `newArchEnabled` toggles.

Enforce runtime compatibility: set an explicit `runtimeVersion` policy (for example `appVersion` or a fingerprint policy — verify the current supported policies for your SDK) so an OTA update can never land on an incompatible binary.

## Build profiles

```jsonc
// eas.json
{
  "build": {
    "development": { "developmentClient": true, "distribution": "internal", "channel": "development" },
    "preview":     { "distribution": "internal", "channel": "staging" },
    "production":  { "autoIncrement": true, "channel": "production" }
  },
  "submit": { "production": {} }
}
```

- One channel per environment; never point a preview build at the production update branch.
- Secrets come from EAS secrets or the CI provider, never from committed `.env` files. `EXPO_PUBLIC_*` is bundle-visible and holds nothing sensitive.
- Bare projects use the same lane shape with Fastlane: `fastlane beta` / `fastlane release`, with match/signing owned by whoever owns the native projects.

## Versioning and rollout

- `version` is product-facing semver; build numbers auto-increment in CI.
- Release branches are cut from `main`; hotfixes are cherry-picked, never developed on the release branch only.
- Store rollouts: staged (for example 10% → 50% → 100%) with a crash-free-sessions threshold gating each step.
- OTA rollback plan: republish the previous update to the branch, and know the time it takes to propagate. Document it before the first incident, not during.

## Observability required before first production release

- Crash reporter installed with release + build number tagging, and source maps uploaded per build (a stack trace without symbols is not a report).
- Breadcrumbs on navigation and on every mutation.
- `ContractError` reported at high severity with the failing path and the schema issue, never the full payload (PII).
- One dashboard with: crash-free sessions, cold start time, API error rate by taxonomy type, and OTA adoption per version.
- Log policy: no `console.log` in shipped code; a logger that no-ops in production and routes to breadcrumbs otherwise.

## Agent-facing rules

If an agent works in this repository, put these in `AGENTS.md`/`CLAUDE.md` — short, enforceable:

- Run `pnpm verify` before reporting a task done; paste the failing output if it fails.
- Never edit files under `src/core/api/generated/` — run `pnpm codegen`.
- Never add a dependency with native code without saying so and flagging that a build is required.
- Never disable a lint rule, a TypeScript flag, or a test to make `verify` pass; report the blocker instead.
- New feature code follows `references/project-structure.md` layering; boundary lint failures are architecture failures, not formatting.
