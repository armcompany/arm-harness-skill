# State Boundaries and Hook Design

## The boundary

| State kind | Examples | Owner | Never |
| --- | --- | --- | --- |
| Server state | entities, lists, pagination, anything with a source of truth on a backend | TanStack Query | copied into a store |
| Client state | filters, wizard step, draft form, selection, sheet open/closed, theme | Zustand (global) or `useState` (local) | fetched or invalidated |
| Session | tokens, current user id | Zustand + secure storage, single store | duplicated per feature |
| Ephemeral UI | animation values, gesture state, input text | component / Reanimated shared values | in a global store |
| Derived | totals, labels, sorted lists | computed during render or in a selector | stored |

Rule: if a value can be re-fetched, it is server state. If it disappears on logout and nobody misses it, it is client state.

**Do not mirror.** The wrong pattern:

```ts
// WRONG: store becomes a stale second source of truth
const { data } = useOrdersQuery();
useEffect(() => { orderStore.setOrders(data ?? []); }, [data]);
```

The right pattern is to share the query key and let every consumer subscribe to the same cache entry:

```ts
const { data: orders = [] } = useOrdersQuery(filters);
```

## Zustand conventions

```ts
// features/catalog/model/catalogFiltersStore.ts
type CatalogFiltersState = {
  category: CategoryId | null;
  sort: 'relevance' | 'price_asc' | 'price_desc';
  setCategory: (id: CategoryId | null) => void;
  setSort: (sort: CatalogFiltersState['sort']) => void;
  reset: () => void;
};

export const useCatalogFiltersStore = create<CatalogFiltersState>()((set) => ({
  category: null,
  sort: 'relevance',
  setCategory: (category) => set({ category }),
  setSort: (sort) => set({ sort }),
  reset: () => set({ category: null, sort: 'relevance' }),
}));
```

- One store per bounded concern, not one god store. Cross-store coordination goes in a hook, not in a store.
- **Always select narrowly**: `useCatalogFiltersStore((s) => s.sort)`. Selecting the whole store re-renders on every unrelated change. Use `useShallow` when selecting multiple fields.
- Actions live inside the store; components call actions, never `set` directly.
- Persist deliberately (`persist` middleware + MMKV storage adapter), and only fields that must survive a cold start. Version the persisted shape and write a migration when it changes.
- Never put functions returning JSX, refs, or class instances in a store.
- Store files live in `features/<domain>/model/` — or `core/` only for genuinely global state (session, theme, connectivity).

## TanStack Query conventions

- Configure once in `core/api/queryClient.ts`: `staleTime`, `gcTime`, retry policy, and a global error handler that maps to the error taxonomy in `references/data-layer.md`.
- Query keys come from a per-feature factory. Never inline string arrays at call sites.
- One hook per query/mutation, exported from `features/<domain>/api/`. Components never call `useQuery` directly.
- Mutations declare their invalidation explicitly; optimistic updates always implement `onError` rollback and `onSettled` invalidation.
- Add `focusManager`/`onlineManager` wiring for React Native (`AppState` and NetInfo) so refetch-on-focus behaves like it does on web.

See `references/data-layer.md` for key factories, mutation shape, and offline persistence.

## Hook layers

Three layers. A hook belongs to exactly one.

| Layer | Naming | Responsibility | Returns |
| --- | --- | --- | --- |
| Data hooks | `useOrderQuery`, `useCancelOrderMutation` | wrap one query/mutation, map DTO to domain | query/mutation result |
| Domain hooks | `useOrderStatus`, `useCartTotals` | pure-ish domain rules over given input | computed values |
| View-model hooks | `useOrderScreen`, `useCheckoutForm` | orchestrate data + client state + navigation + handlers for one screen | a flat view model |

Rules:

- A view-model hook is the **only** place a screen's data, state, and handlers combine. One per screen, colocated with it.
- View-model hooks return a flat, serializable-ish object: primitives, arrays, and stable callbacks. No query objects leaked, no `refetch` passed through unless the UI genuinely offers a retry.
- Domain hooks contain no `useEffect` and no imports from `api/`. Most of them should be plain functions instead — only make it a hook if it uses React state or context.
- Data hooks never read from Zustand. Pass parameters in; the caller composes.
- A hook returning more than ~8 keys is doing two jobs. Split by responsibility, not by size.
- No hook calls another view-model hook. Composition happens downward only.

### View-model hook example

```ts
// features/orders/model/useOrderScreen.ts
export function useOrderScreen(orderId: OrderId) {
  const router = useRouter();
  const { data: order, isPending, isError, refetch } = useOrderQuery(orderId);
  const { mutateAsync: cancelOrder, isPending: isCancelling } = useCancelOrderMutation();
  const [confirmVisible, setConfirmVisible] = useState(false);

  const canCancel = order ? isCancellable(order) : false; // pure domain fn

  const onConfirmCancel = useCallback(async () => {
    setConfirmVisible(false);
    try {
      await cancelOrder(orderId);
      router.back();
    } catch (error) {
      reportError(error, { scope: 'orders.cancel', orderId });
    }
  }, [cancelOrder, orderId, router]);

  return {
    status: isPending ? 'loading' : isError ? 'error' : 'ready',
    order,
    canCancel,
    isCancelling,
    confirmVisible,
    onPressCancel: () => setConfirmVisible(true),
    onDismissConfirm: () => setConfirmVisible(false),
    onConfirmCancel,
    onRetry: refetch,
  } as const;
}
```

### Screen using it

```tsx
// features/orders/ui/OrderScreen.tsx
export function OrderScreen({ orderId }: { orderId: OrderId }) {
  const vm = useOrderScreen(orderId);

  if (vm.status === 'loading') return <ScreenLoader />;
  if (vm.status === 'error') return <ErrorState onRetry={vm.onRetry} />;

  return (
    <ScreenLayout>
      <OrderSummary order={vm.order!} />
      {vm.canCancel && (
        <Button label="Cancel order" loading={vm.isCancelling} onPress={vm.onPressCancel} />
      )}
      <ConfirmSheet
        visible={vm.confirmVisible}
        onConfirm={vm.onConfirmCancel}
        onDismiss={vm.onDismissConfirm}
      />
    </ScreenLayout>
  );
}
```

The screen has no `useQuery`, no store access, no `try/catch`, no formatting. It is testable by rendering with a stubbed view model, and the view model is testable without rendering anything.

## Render / logic separation contract

A component may:

- read props and context,
- call exactly one view-model hook (screens only),
- compose other components,
- run layout and style logic.

A component may not:

- import from `core/api/` or `features/*/api/`,
- create or subscribe to a store other than through its view model,
- contain `try/catch` around network calls,
- format currency, dates, or pluralization inline — call `shared/lib` formatters,
- hold business branching deeper than presentational conditionals.

Presentational components take data, not ids. `<OrderCard order={order} />`, never `<OrderCard orderId={id} />` with a fetch inside — that pattern creates N+1 requests and untestable leaves.

## `useEffect` policy

Allowed: subscriptions to external systems (AppState, NetInfo, native events, timers), imperative side effects on mount/unmount, and syncing to non-React systems (analytics, deep-link handlers).

Not allowed: deriving state, resetting state on prop change (use `key` instead), copying query data into a store, or chaining state updates. Every `useEffect` in a `ui/` file needs a one-line comment explaining which external system it subscribes to; if it cannot be written, delete the effect.

## Performance rules that are architecture, not micro-optimization

- Lists use `FlashList` or `FlatList` with stable `keyExtractor`, memoized row components, and no inline object/array props.
- Context is split by change frequency. A single `AppContext` holding session + theme + everything re-renders the tree on any change.
- Heavy transforms live in `select` (TanStack Query) or a memoized selector, not in the render body.
- Animations use Reanimated shared values, which never enter React state.
- Navigation params carry ids and small primitives only; the destination fetches from cache.
