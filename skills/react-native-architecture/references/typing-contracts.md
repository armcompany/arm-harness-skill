# Typing and Contracts

Goal: every value that enters the app from outside is either generated from a schema or validated at runtime. TypeScript alone does not protect a mobile app — it describes intentions about data it never sees.

## TypeScript configuration floor

```jsonc
// tsconfig.json
{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "verbatimModuleSyntax": true,
    "skipLibCheck": true
  }
}
```

- `noUncheckedIndexedAccess` is the single highest-value flag for mobile: it catches the `list[0]` crash class.
- Turning a flag off to unblock a migration is allowed once, with a dated TODO and a ticket. Turning it off permanently is an architecture decision that needs an ADR.
- `any` is banned outside of `*.d.ts` shims for untyped native modules. Use `unknown` and narrow.
- Lint gates: `@typescript-eslint/no-unsafe-*` rules on at least `features/*/api` and `core/`.

## Runtime validation at boundaries

Validate at exactly these five boundaries — nowhere else:

1. Network responses (see `references/data-layer.md`).
2. Deep link and navigation params.
3. Persisted storage reads (MMKV/SQLite/SecureStore) — persisted shapes outlive app versions.
4. Native module and third-party SDK callbacks.
5. Remote config / feature flag payloads.

```ts
// features/orders/api/orderSchema.ts
const OrderDto = z.object({
  id: z.string().min(1),
  status: z.enum(['pending', 'paid', 'shipped', 'cancelled']),
  total_cents: z.number().int(),
  created_at: z.string().datetime(),
});

export type OrderDto = z.infer<typeof OrderDto>;

export function toDomainOrder(dto: OrderDto): Order {
  return {
    id: dto.id as OrderId,
    status: dto.status,
    total: Money.fromCents(dto.total_cents),
    createdAt: new Date(dto.created_at),
  };
}
```

DTO and domain types are different types. The DTO mirrors the wire format (`snake_case`, cents, ISO strings); the domain type is what the app reasons about. Mapping happens once, in `api/`.

Do not validate internal function arguments with Zod — that is what the compiler is for, and it costs runtime on every render.

## Generated clients

**REST with OpenAPI:**

```bash
npx openapi-typescript ./contracts/openapi.yaml -o ./src/core/api/generated/schema.d.ts
```

Pair with `openapi-fetch` for a typed client, or keep `request()` and use generated types for the DTO layer. Commit generated files and regenerate in CI with a diff check — a drifted client that only regenerates locally is worse than a handwritten one.

**GraphQL:**

```ts
// codegen.ts
const config: CodegenConfig = {
  schema: 'https://api.example.com/graphql',
  documents: ['src/**/*.{ts,tsx}'],
  generates: { './src/core/api/generated/': { preset: 'client', config: { scalars: { DateTime: 'string' } } } },
};
```

Map custom scalars explicitly. An unmapped scalar becomes `any` and silently defeats the whole pipeline.

CI gate: `pnpm codegen && git diff --exit-code src/core/api/generated`. Contract drift fails the build instead of surfacing as a runtime crash.

## Branded domain ids

```ts
declare const brand: unique symbol;
export type Brand<T, B extends string> = T & { readonly [brand]: B };

export type OrderId = Brand<string, 'OrderId'>;
export type UserId = Brand<string, 'UserId'>;
```

Prevents the classic mobile bug of passing a `userId` into a route expecting an `orderId`. Cast only at the mapping boundary (`dto.id as OrderId`), never in components.

## Navigation typing

**expo-router:** enable typed routes (`experiments.typedRoutes` in app config, verify the current flag name for your SDK) so `href` strings are checked. Params still arrive as strings from deep links — parse them:

```ts
const { id } = useLocalSearchParams<{ id: string }>();
const orderId = OrderIdSchema.parse(id);   // throws -> not-found boundary
```

**React Navigation:** declare `RootStackParamList` and augment the global namespace so `navigation.navigate` is checked app-wide. Never type params as `Record<string, unknown>`.

Every screen reachable by deep link must handle invalid params with a not-found state, not a crash. Test this: a malformed deep link is a real user path from email and push notifications.

## Environment and config typing

```ts
// core/config/index.ts
const Env = z.object({
  EXPO_PUBLIC_API_URL: z.string().url(),
  EXPO_PUBLIC_ENV: z.enum(['development', 'staging', 'production']),
});

export const config = Env.parse(process.env);   // fails at startup, not at first request
```

- `EXPO_PUBLIC_*` values are inlined into the bundle. They are **public**. Secrets never live there — they live on the server or in EAS secrets used at build time only.
- Validate at module load so a misconfigured build fails immediately and visibly.

## Shared contracts in a modular app

`packages/domain-contracts` holds the types and Zod schemas both the host and modules use: event bus payloads, session shape, route descriptors. Rules:

- Contracts package has no runtime dependencies beyond the validation library.
- Every event payload is a named schema; the bus validates in development builds and trusts in production.
- Breaking a contract type requires bumping the contracts package and updating consumers in the same change — that is the entire point of having the package.

## Typing checklist for a review

- [ ] `strict` plus `noUncheckedIndexedAccess` enabled, no per-file `@ts-expect-error` without a comment and ticket
- [ ] No `any` in `features/*/api` or `core/`
- [ ] Every network response parsed by a schema
- [ ] DTO types distinct from domain types; mapping in `api/` only
- [ ] Generated code committed and verified by a CI diff check
- [ ] Custom GraphQL scalars mapped
- [ ] Route params typed and parsed, invalid params handled
- [ ] Env validated at startup, no secrets in `EXPO_PUBLIC_*`
- [ ] Ids branded for at least the entities that share the `string` type
