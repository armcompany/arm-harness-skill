# Testing Strategy

The architecture above exists partly so tests are cheap. Pure domain functions, view-model hooks, and presentational components are each testable in isolation — if a piece is hard to test, the separation was violated.

## Tiers and mocking rule

**A tier may only mock the tier below it.**

| Tier | Runner | Scope | May mock | Target share | Gate |
| --- | --- | --- | --- | --- | --- |
| Unit | Jest (`jest-expo`) | pure domain functions, mappers, selectors, formatters | time, randomness, nothing else | ~50% | pre-commit + PR |
| Hook | Jest + `@testing-library/react-hooks` API in RTL | view-model and data hooks with a real QueryClient | transport (MSW) | ~20% | PR |
| Component | Jest + `@testing-library/react-native` | presentational components, screens with stubbed view model | view-model hook or transport | ~20% | PR |
| Contract | Jest + generated types / schema fixtures | DTO schemas against recorded real payloads | nothing | ~5% | PR + nightly against staging |
| E2E | Maestro or Detox | critical user flows on a real build | backend environment only | ~5% | pre-release + nightly |

Percentages are a shape, not a quota. The hard rule is the mocking direction: a component test that mocks a domain function is testing nothing.

## Unit tests

Domain logic is plain functions, so tests are plain:

```ts
describe('isCancellable', () => {
  it.each([
    ['pending', true],
    ['paid', true],
    ['shipped', false],
    ['cancelled', false],
  ])('order %s -> %s', (status, expected) => {
    expect(isCancellable(makeOrder({ status }))).toBe(expected);
  });
});
```

Use factories (`makeOrder`) with sensible defaults and explicit overrides. Never share a mutable fixture object between tests.

## Hook tests

Use a fresh `QueryClient` per test with retries off, and MSW to serve the transport.

```tsx
function renderWithClient<T>(hook: () => T) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  return renderHook(hook, {
    wrapper: ({ children }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>,
  });
}

it('exposes a cancel action only for cancellable orders', async () => {
  server.use(http.get('*/orders/1', () => HttpResponse.json(orderFixture({ status: 'paid' }))));
  const { result } = renderWithClient(() => useOrderScreen('1' as OrderId));
  await waitFor(() => expect(result.current.status).toBe('ready'));
  expect(result.current.canCancel).toBe(true);
});
```

MSW (`msw/native`) is the default transport mock: it tests the real client, real schema parsing, and real error mapping. Mocking `fetch` by hand skips exactly the code most likely to be wrong.

## Component tests

- Query by accessible role, label, or text — not by `testID` where a user-facing query exists. `testID` is for E2E anchors.
- Screens are tested by stubbing the view-model hook (`jest.mock('../model/useOrderScreen')`); this isolates layout and interaction wiring.
- Presentational components are tested with props only. If a presentational test needs a provider, the component is not presentational.
- Assert behavior, not structure. Snapshots are allowed only for stable design-system primitives, and a snapshot larger than ~30 lines is noise nobody will review.
- Test the three states every data screen has: loading, error with retry, and empty. Empty state bugs reach production more often than happy-path bugs.

## Contract tests

Keep recorded real payloads in `fixtures/contracts/*.json` and assert the schema still parses them:

```ts
it('parses the recorded order payload', () => {
  expect(() => OrderDto.parse(recorded.order)).not.toThrow();
});
```

Run the same suite nightly against staging with live responses. This is how backend drift is caught before it becomes a `ContractError` in production.

## E2E: Maestro vs Detox

| Choose | When |
| --- | --- |
| **Maestro** | Default. YAML flows, no app instrumentation, tolerant of async, runs against release-like builds, easy for QA to author and read. |
| **Detox** | You need grey-box synchronization guarantees, deterministic control of animations/timers, or you already have a maintained Detox suite and native-side hooks. |

Rules either way:

- E2E covers **critical revenue and trust flows only**: login, the main conversion path, payment, and one destructive action. Every additional flow is maintenance you pay forever.
- Run against a build produced by the real pipeline (EAS preview/simulator build), not a dev-client with Metro attached — otherwise you are testing your laptop.
- Backend: prefer a seeded staging environment with deterministic accounts. If mocking, mock at the network boundary of the built app, not by shipping a fake data layer into the binary.
- Stable anchors: reserved `testID`s on the elements the flows touch, defined in the component, reviewed like an API. Never generated or index-based.
- A flaky E2E test is deleted or fixed within one sprint. A permanently retried suite trains everyone to ignore red.

Example Maestro flow:

```yaml
appId: com.example.app
---
- launchApp:
    clearState: true
- tapOn: { id: 'login.email' }
- inputText: 'qa+e2e@example.com'
- tapOn: { id: 'login.submit' }
- assertVisible: { id: 'home.header' }
- tapOn: { id: 'orders.tab' }
- assertVisible: 'Your orders'
```

## What is not covered by unit or E2E

Declare these explicitly rather than pretending the pyramid covers them:

- **Native permissions and OS dialogs** — manual or device-farm checks.
- **Push notification delivery and cold-start deep links** — scripted manual checks per release, at minimum.
- **Performance** — startup time, list scroll frame rate, bundle size; measure with a release build and record numbers per release.
- **Accessibility** — automated checks catch missing labels; dynamic type, contrast, and screen reader order need a manual pass.
- **Visual regression** — optional; if adopted, run it on a fixed device profile or it will be permanently red.

## Gates

| Gate | Runs | Blocks |
| --- | --- | --- |
| pre-commit (staged files) | typecheck on changed project, lint, unit tests for touched paths | commit |
| PR CI | `typecheck`, `lint`, `test --coverage`, codegen diff check, unit+hook+component+contract | merge |
| Nightly | E2E on iOS and Android, contract tests against staging | alert, not merge |
| Pre-release | full E2E, performance snapshot, manual permission/push checklist | release |

Coverage thresholds: enforce on `features/*/model/**` and `features/*/api/**` (the logic that matters), not globally. A global 80% threshold makes people test `ui/` files to reach a number.

## Test infrastructure conventions

- `jest-expo` preset with `transformIgnorePatterns` covering the RN/Expo module set; verify against your SDK version rather than copying a preset from an old project.
- One `test/setup.ts` that starts MSW, silences known native warnings explicitly (never blanket-silences console), and installs custom matchers.
- Fixtures and factories in `test/factories/`, shared across tiers.
- No test reaches the network. MSW's `onUnhandledRequest: 'error'` enforces it.
