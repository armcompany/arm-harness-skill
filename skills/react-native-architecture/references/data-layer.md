# Data Layer

The data layer is the only part of the app allowed to know about HTTP, GraphQL, headers, retries, and DTO shapes. Everything above it sees domain types.

## Transport isolation

```
core/api/httpClient.ts      # base URL, auth header, timeout, error normalization
core/api/graphqlClient.ts   # same, for GraphQL POST
core/api/queryClient.ts     # TanStack Query defaults
features/<domain>/api/*.ts  # endpoints, DTO -> domain mapping, query hooks
```

One client instance, created in `core/`, injected or imported only by `features/*/api`. Two clients means two places auth refresh can be wrong.

```ts
// core/api/httpClient.ts
export async function request<T>(
  path: string,
  init: RequestInit & { schema: ZodType<T>; signal?: AbortSignal },
): Promise<T> {
  const response = await fetch(`${config.apiBaseUrl}${path}`, {
    ...init,
    headers: { 'content-type': 'application/json', ...authHeader(), ...init.headers },
  });

  if (!response.ok) throw await toAppError(response);

  const json: unknown = await response.json();
  const parsed = init.schema.safeParse(json);
  if (!parsed.success) throw new ContractError(path, parsed.error);
  return parsed.data;
}
```

Every response passes a schema. A payload that changed shape must fail loudly in staging, not silently render `undefined` in production.

## Query key factories

```ts
// features/orders/api/orderKeys.ts
export const orderKeys = {
  all: ['orders'] as const,
  lists: () => [...orderKeys.all, 'list'] as const,
  list: (filters: OrderFilters) => [...orderKeys.lists(), filters] as const,
  details: () => [...orderKeys.all, 'detail'] as const,
  detail: (id: OrderId) => [...orderKeys.details(), id] as const,
};
```

- Keys are hierarchical so invalidation can be coarse (`orderKeys.lists()`) or precise (`orderKeys.detail(id)`).
- Filters in a key must be a stable, serializable object; normalize before use (sorted keys, no `undefined`).
- Never inline a key array at a call site. The factory is the contract.

## Query hooks

```ts
// features/orders/api/useOrderQuery.ts
export function useOrderQuery(orderId: OrderId) {
  return useQuery({
    queryKey: orderKeys.detail(orderId),
    queryFn: ({ signal }) => getOrder(orderId, signal),   // returns domain Order
    staleTime: 30_000,
    select: undefined,                                     // shape mapping already done in getOrder
  });
}
```

- `queryFn` returns a **domain** type. DTO-to-domain mapping lives in `getOrder`, not in `select` and not in the component.
- Pass `signal` through to `fetch` so navigation-away cancels in-flight requests.
- `staleTime` is a product decision per resource: near-zero for balances and order status, minutes for catalog, effectively infinite for static config. A blanket global `staleTime: 0` causes request storms on mobile.

## Mutations

```ts
export function useCancelOrderMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (orderId: OrderId) => cancelOrder(orderId),

    onMutate: async (orderId) => {
      await queryClient.cancelQueries({ queryKey: orderKeys.detail(orderId) });
      const previous = queryClient.getQueryData<Order>(orderKeys.detail(orderId));
      if (previous) {
        queryClient.setQueryData<Order>(orderKeys.detail(orderId), { ...previous, status: 'cancelling' });
      }
      return { previous };
    },

    onError: (_error, orderId, context) => {
      if (context?.previous) queryClient.setQueryData(orderKeys.detail(orderId), context.previous);
    },

    onSettled: (_data, _error, orderId) => {
      queryClient.invalidateQueries({ queryKey: orderKeys.detail(orderId) });
      queryClient.invalidateQueries({ queryKey: orderKeys.lists() });
    },
  });
}
```

Rule: an optimistic update without `onError` rollback is a bug waiting for a flaky network. If you will not write the rollback, do not write the optimism.

## GraphQL

Two supported shapes:

**A. GraphQL through TanStack Query** (default when you do not need a normalized cache):

```ts
const document = graphql(`query Order($id: ID!) { order(id: $id) { id status total } }`);

export function useOrderQuery(id: OrderId) {
  return useQuery({
    queryKey: orderKeys.detail(id),
    queryFn: ({ signal }) => gqlRequest(document, { id }, signal).then(toDomainOrder),
  });
}
```

Types come from `graphql-codegen` with the client preset; the `graphql()` function is generated and typed. One cache, same invalidation model as REST — the transport becomes an implementation detail.

**B. Apollo Client / urql with a normalized cache** when entities appear across many screens and a single mutation must update all of them without explicit invalidation. Costs: cache policy configuration, `keyFields`, pagination policies, and a second caching mental model. Choose deliberately, and if you choose it, do **not** also use TanStack Query for the same domain.

Fragment colocation rule: a component that needs fields declares a fragment; screens compose fragments into the query. This is the main reason to pick GraphQL, so if the team will not do it, reconsider the transport.

## Error taxonomy

Normalize every failure into one of these before it leaves the data layer:

| Type | Meaning | UI behavior | Retry |
| --- | --- | --- | --- |
| `NetworkError` | no connectivity, timeout, DNS | offline state, retry affordance | yes, backoff |
| `AuthError` | 401/403, expired refresh | route to login, clear cache | no |
| `ValidationError` | 422, field-level backend rejection | inline field errors | no |
| `NotFoundError` | 404 on a resource the user navigated to | empty/not-found screen | no |
| `ContractError` | schema parse failure | generic error + report to crash reporter with payload shape | no |
| `ServerError` | 5xx | generic error with retry | yes, limited |
| `UnknownError` | anything unmapped | generic error, always reported | no |

`ContractError` must be reported with high severity: it means the client and backend disagree and the type system was lying.

Retry policy: retry `NetworkError` and `ServerError` with exponential backoff and a cap; never retry mutations automatically unless they are idempotent and carry an idempotency key.

## Offline and persistence

Decide the offline tier explicitly:

1. **None** — online-only app; show a connectivity state. Cheapest, valid for many apps.
2. **Read-offline** — persist the query cache (`@tanstack/query-async-storage-persister` or an MMKV persister), set `gcTime` above the persistence window, and mark stale data visibly in the UI.
3. **Write-offline** — a mutation queue with idempotency keys, conflict policy, and replay on reconnect. This is a feature with its own tests, not a config flag. Do not promise it casually.

Wire React Native specifics regardless of tier:

```ts
onlineManager.setEventListener((setOnline) =>
  NetInfo.addEventListener((state) => setOnline(Boolean(state.isConnected))));

AppState.addEventListener('change', (status) => focusManager.setFocused(status === 'active'));
```

## Pagination

- Use `useInfiniteQuery` with cursor pagination when the backend supports it; offset pagination duplicates rows when the list mutates.
- `getNextPageParam` returns `undefined` at the end — never `null` guessing.
- Flatten pages in a `select` or a memo, never in the render body of a list screen.

## Auth and cache lifecycle

- Tokens in SecureStore/Keychain, never AsyncStorage, never in a persisted Zustand slice that writes to plain storage.
- Refresh is single-flight: concurrent 401s wait on one refresh promise, not N.
- On logout: `queryClient.clear()`, reset client stores, drop persisted cache. A stale cache surviving logout is a data-leak bug.
