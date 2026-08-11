# Project Structure

Two supported topologies. Both are feature-first: code is grouped by domain, never by technical kind at the top level. `components/`, `hooks/`, `utils/` as root folders is how apps rot — they force every feature to spread across four directories.

## Layer contract (applies to both topologies)

| Layer | Owns | May import | Must not import |
| --- | --- | --- | --- |
| `app/` (routes) | Route files, layouts, navigation wiring | features (public API), shared UI | transport clients, stores, feature internals |
| `features/<domain>/ui` | Presentational components, screens | own feature hooks, shared UI, design tokens | transport, storage, other features' internals |
| `features/<domain>/model` | Hooks, view models, state machines, selectors | own feature api, shared domain, stores | React Native view primitives, other features' internals |
| `features/<domain>/api` | Queries, mutations, DTO mapping, query keys | shared transport, generated types | React, navigation, UI |
| `shared/` | Cross-domain UI kit, hooks, utils, types | other `shared/` modules | any `features/` module |
| `core/` | Transport clients, storage, config, observability, providers | shared types | features, UI |

Direction of dependency is one-way: `app -> features -> shared -> core`. A `features/a` importing `features/b/model/...` is a violation; go through `features/b/index.ts` public API or move the shared piece down to `shared/`.

## Topology A — Monolith, feature-first

```
app/                          # expo-router routes only; thin
  _layout.tsx
  (tabs)/
    index.tsx
    profile.tsx
  order/[id].tsx
src/
  features/
    orders/
      api/
        orderKeys.ts          # query key factory
        getOrder.ts           # transport call + DTO -> domain mapping
        useOrderQuery.ts      # TanStack Query wrapper
        useCancelOrder.ts     # mutation + cache invalidation
      model/
        useOrderScreen.ts     # the screen's view model; no JSX
        orderStatus.ts        # pure domain logic
        orderStore.ts         # client-only state (filters, draft), if needed
      ui/
        OrderScreen.tsx       # composition; consumes useOrderScreen()
        OrderCard.tsx         # pure, props-in
        OrderStatusBadge.tsx
      __tests__/
        orderStatus.test.ts
        useOrderScreen.test.tsx
        OrderCard.test.tsx
      index.ts                # public API: screens + types the app may use
    auth/
    catalog/
  shared/
    ui/                       # Button, Text, Sheet, design tokens
    hooks/                    # useDebounce, useAppState
    lib/                      # pure helpers: format, date, money
    types/
  core/
    api/
      httpClient.ts           # single place that knows about fetch/headers/auth
      graphqlClient.ts
      queryClient.ts          # TanStack Query config, retry, gc, persistence
    storage/                  # MMKV / SecureStore wrappers
    config/                   # typed env
    observability/            # crash reporter, breadcrumbs, logger
    providers/                # AppProviders composition
e2e/                          # Maestro flows or Detox specs
scripts/                      # repo automation
```

Rules:

- `app/` route files contain no business logic. A route imports a screen from a feature and renders it. If a route file is longer than ~30 lines, logic leaked upward.
- `index.ts` per feature exports only what other features and routes may use. It is not a barrel of everything.
- No cross-feature imports except through `index.ts`. Shared concepts move down to `shared/` or `core/`.
- A feature with no `model/` folder is suspicious: it means logic is living in components.

## Topology B — Modular superapp

Workspace-based (pnpm or yarn workspaces + TypeScript project references). Each module is a package with its own `package.json`, tests, and public API.

```
apps/
  host/                       # the shell: routing, providers, module registry
    app/
    src/
      registry/moduleRegistry.ts
      providers/
packages/
  core-runtime/               # transport, storage, config, observability, event bus
  design-system/              # UI kit + tokens; the only place styling primitives live
  domain-contracts/           # shared types, Zod schemas, event payload types
  module-orders/
    src/
      api/ model/ ui/
      index.ts                # implements the ModuleContract
    package.json
  module-payments/
  module-catalog/
tooling/
  eslint-config/
  tsconfig/
e2e/
```

### Module contract

Every module exports one object. The host never imports module internals.

```ts
// packages/domain-contracts/src/module.ts
export type ModuleContract = {
  id: string;                       // stable, used for flags and analytics
  routes: RouteDescriptor[];        // what the host mounts
  entryPoints?: EntryPointDescriptor[]; // tab items, home cards, deep links
  onRegister?: (ctx: HostContext) => void;
  onTeardown?: () => void;
};

export type HostContext = {
  http: HttpClient;
  events: EventBus;          // cross-module communication, typed payloads
  flags: FlagReader;
  navigate: (href: string) => void;
  session: SessionReader;    // read-only; modules never mutate auth
};
```

Rules:

- Modules communicate through the typed event bus and the host navigation API — never by importing each other.
- Only `core-runtime` constructs clients. Modules receive them via `HostContext`; this keeps modules testable with a fake context.
- `domain-contracts` is the only package two modules may both depend on, and it holds types and schemas only — no runtime behavior beyond validation.
- Every module ships its own test lane and can be built and tested in isolation in CI. If it cannot, it is not a module.
- Version modules with the app unless they are genuinely released independently; independent versioning without independent release is pure overhead.

## Boundary enforcement (do this, not a wiki page)

ESLint, monolith:

```js
// eslint.config.js (flat config excerpt)
'import/no-restricted-paths': ['error', {
  zones: [
    { target: './src/shared', from: './src/features', message: 'shared must not import features' },
    { target: './src/core',   from: './src/features', message: 'core must not import features' },
    { target: './src/core',   from: './src/shared',   message: 'core must not import shared UI' },
    { target: './src/features/*/ui', from: './src/core/api', message: 'UI must not touch transport' },
  ],
}],
'no-restricted-imports': ['error', {
  patterns: [
    { group: ['../../features/*/*'], message: 'cross-feature deep import; use the feature public API' },
    { group: ['**/core/api/httpClient*'], importNames: ['httpClient'], message: 'call transport from features/*/api only' },
  ],
}],
```

Workspaces: rely on package boundaries plus `eslint-plugin-boundaries` or `dependency-cruiser` for the host/module direction, and TypeScript project references so a wrong import fails typecheck rather than review.

Add path aliases so imports are stable:

```jsonc
// tsconfig.json
{ "compilerOptions": { "paths": {
  "@/features/*": ["./src/features/*"],
  "@/shared/*":   ["./src/shared/*"],
  "@/core/*":     ["./src/core/*"]
}}}
```

Mirror them in `babel.config.js` (`babel-plugin-module-resolver`) or rely on Metro's `tsconfig` paths support, and verify one alias import actually resolves at runtime before committing the config.

## Monolith to modular extraction path

1. Ensure the feature has no cross-feature deep imports (lint gate above catches this).
2. Move shared pieces it depends on into `shared/` or `design-system/`.
3. Replace direct client imports with injected dependencies (`HostContext` shape) inside the feature.
4. Move the folder to `packages/module-<name>/src`, add `package.json` and `tsconfig.json` with references.
5. Register through the module registry; delete the old route imports.
6. Prove isolation: the module's tests pass with only its own package installed and a fake host context.

Do steps 1–3 even if you never do 4–6. They are the actual value; the package move is bookkeeping.
