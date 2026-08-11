# Templates

Copy, fill, delete what does not apply. Empty ceremony weakens the architecture as much as no structure.

## ADR

```markdown
# ADR-00X: <decision in one line>

- Status: proposed | accepted | superseded by ADR-00Y
- Date: YYYY-MM-DD
- Deciders: <names/roles>

## Context
<the constraint that forces a choice: team topology, backend ownership, release cadence, native requirement>

## Decision
<what we chose, stated so a new engineer can apply it without asking>

## Alternatives
| Option | Why not |
| --- | --- |
| <alt> | <cost/blocker> |

## Consequences
- Enables: <...>
- Costs: <...>
- Revisit when: <observable trigger, e.g. "two teams block each other in review for two sprints">

## Enforcement
<the lint rule, script, type, test, or CI gate that makes this real — or "judgment call, unenforced" with a reason>
```

## Architecture decision summary (interview output)

```markdown
## Resolved
| Decision | Choice | Evidence | ADR |
| --- | --- | --- | --- |
| Workflow | Expo CNG | no native blockers found; no ios/ or android/ committed | ADR-001 |
| Topology | Monolith, feature-first | 4 engineers, one team | ADR-002 |
| Transport | REST + TanStack Query | OpenAPI spec exists, 3 backend owners | ADR-003 |

## Assumed
| Decision | Assumption | Correct by |
| --- | --- | --- |

## Blocked
| Decision | Needs | From |
| --- | --- | --- |
```

## Module contract (modular topology)

```markdown
# Module: <name>

- ID: `module-<name>`
- Owner: <team>
- Public API: `src/index.ts` exports `ModuleContract`
- Routes: `/<name>`, `/<name>/[id]`
- Entry points: <tab | home card | deep link | none>
- Host capabilities used: http, events, flags, navigate, session
- Events published: `<name>.<event>` (schema in domain-contracts)
- Events consumed: `<other>.<event>`
- Feature flag: `module_<name>_enabled`
- Isolation test: `pnpm --filter module-<name> test` passes with a fake HostContext
```

## Feature scaffold checklist

```
features/<domain>/
  api/       <domain>Keys.ts, get<X>.ts, use<X>Query.ts, use<X>Mutation.ts, <domain>Schema.ts
  model/     use<Screen>.ts, <domain>Rules.ts, <domain>Store.ts (only if client state exists)
  ui/        <Screen>.tsx, <Component>.tsx
  __tests__/ rules (unit), view model (hook), components
  index.ts   public API
```

- [ ] No import from another feature's internals
- [ ] No transport import inside `ui/`
- [ ] Every response schema-validated, DTO mapped to domain
- [ ] Loading, error, and empty states implemented and tested
- [ ] Query keys from the factory, invalidation declared on mutations
- [ ] Accessibility labels on interactive elements

## View-model hook

```ts
export function use<Screen>(params: <Params>) {
  // 1. data
  // 2. client state
  // 3. derived domain values (pure functions)
  // 4. handlers (useCallback, stable)
  // 5. flat view model return
  return {
    status: 'loading' | 'error' | 'empty' | 'ready',
    // data fields
    // flags
    // handlers: on<Event>
  } as const;
}
```

## Query hook

```ts
export function use<Entity>Query(<params>) {
  return useQuery({
    queryKey: <entity>Keys.detail(<id>),
    queryFn: ({ signal }) => get<Entity>(<id>, signal),
    staleTime: <justified value>,
  });
}
```

## Zustand store

```ts
type <Name>State = {
  // state
  // actions
  reset: () => void;
};

const initial = { /* ... */ } satisfies Partial<<Name>State>;

export const use<Name>Store = create<<Name>State>()((set) => ({
  ...initial,
  // actions
  reset: () => set(initial),
}));
```

## Audit report

```markdown
# React Native Architecture Audit — <app>

## Detected stack
| Item | Value |
| --- | --- |
| Workflow | Expo CNG / Expo prebuild committed / Bare |
| React Native / Expo SDK | <versions> |
| Navigation | expo-router / react-navigation |
| Server state | <lib> |
| Client state | <lib> |
| Transport | REST / GraphQL / both |
| Tests | <runners present> |
| E2E | Maestro / Detox / none |

## Violations
| Severity | Contract | Location | Fix | Proven by |
| --- | --- | --- | --- | --- |
| high | UI imports transport | src/features/x/ui/Y.tsx:12 | move to api/ + view model | lint zone rule |

## Missing sensors
- <check that does not exist and the failure it would have caught>

## Prioritized plan
1. <fix> — blocks <risk> — verified by <command>
```

## PR checklist

```markdown
- [ ] `pnpm verify` passes locally (output pasted if it failed anywhere)
- [ ] No cross-feature deep imports; boundary lint clean
- [ ] No transport, store, or formatting logic inside `ui/`
- [ ] New network payloads schema-validated; DTO mapped to domain
- [ ] Mutations declare invalidation; optimistic updates have rollback
- [ ] Loading / error / empty states covered by tests
- [ ] No new `any`, no disabled lint rules or TS flags
- [ ] Generated code regenerated, not hand-edited
- [ ] Native-affecting change? flagged, build required, OTA not sufficient
- [ ] ADR added or updated if this changes an architecture decision
```

## AGENTS.md excerpt for a generated app

```markdown
## Architecture rules
- Components render, hooks decide, `api/` fetches. Never import a transport client in `ui/`.
- Server state lives in TanStack Query; client state in Zustand. Never copy query data into a store.
- Cross-feature imports go through the feature's `index.ts`.
- Validate every external payload with a schema; DTO types are separate from domain types.

## Verification
- Run `pnpm verify` before reporting done. Paste failures; do not disable checks to go green.
- Native dependency or config change: say so explicitly — it requires a build, not an OTA update.
- Never edit `src/core/api/generated/**`; run `pnpm codegen`.
```
