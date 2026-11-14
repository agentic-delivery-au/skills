# TypeScript patterns

Code examples for each rule in `SKILL.md`. The underlying principles are language-agnostic; see the
**ad-general:principle-type-system-discipline** and **ad-general:principle-boundary-discipline**
principle skills.

## Branded types

Brand primitives so they can't be mixed up. Validate once at creation; downstream code trusts the
type.

```ts
type AgentId = string & { readonly __brand: "AgentId" };

function parseAgentId(input: string): AgentId {
  if (!isUUID(input)) throw new Error(`Invalid agent id: ${input}`);
  return input as AgentId;
}

function focusAgent(id: AgentId): void {
  /* input is trusted */
}
```

Match the `readonly __brand: 'X'` shape; don't invent a new convention.

## Discriminated unions

If a bug forces the question "wait, can this combination actually happen?", the type is too loose.
Model variants with a literal discriminant: every variant shares the field name and each variant's
value is unique, so impossible combos can't be represented.

```ts
// Don't. Boolean + optionals lets contradictory states exist.
type DiffState = { loading: boolean; diff?: GitDiff; error?: string };

// Do. Only valid states exist.
type DiffState =
  { kind: "loading" } | { kind: "ready"; diff: GitDiff } | { kind: "error"; error: string };
```

Pick one discriminant name (`kind`, `type`, `tag`) and stick to it.

## Constructive modeling

Build the type from parts that are all legal instead of restricting a loose type with runtime
checks. Adding is easier than subtracting.

Non-empty, via a variadic tuple:

```ts
type NonEmpty<T> = [T, ...T[]];

// Don't: T[] plus a check every caller must repeat
function firstEntry(entries: string[]): string {
  const [first] = entries;
  if (first === undefined) throw new Error("no entries");
  return first;
}

// Do: an empty value of the type can't exist
function firstEntry(entries: NonEmpty<string>): string {
  return entries[0];
}
```

Where a plain `T[]` arrives, narrow once with a guard. The fact then travels in the type:

```ts
function isNonEmpty<T>(arr: T[]): arr is NonEmpty<T> {
  return arr.length > 0;
}
```

Declare it, don't write `const isNonEmpty = <T>(...)`. In a `.tsx` file the parser reads `<T>` as a
JSX tag and fails with TS17008. `<T,>` also works, but the declaration reads better and behaves the
same in both file types.

Even length, as pairs. TypeScript has no refinement types (no `arr.length % 2 === 0` at the type
level); you don't need one:

```ts
type Pairs<T> = [T, T][];
```

A time range, as start plus duration:

```ts
// Don't: a comment holds the invariant
type TimeRange = { start: Date; end: Date }; // start <= end

// Do: the ordering invariant is gone; derive end when needed
type TimeRange = { start: Date; durationMs: number };
```

This kills the invariant a comment was holding — `end` before `start` is no longer expressible. It
does not make every bad value unconstructable: `durationMs: -1000` still compiles. If negative
durations matter, that is a branded `Duration` with a constructor that rejects them, which is a
second decision and not free. Do not read "constructive modeling" as "the type now proves
everything".

Keep `durationMs` a plain number. Brand it (per Branded types) only if a raw number could be passed
where a duration is expected, not by reflex. A `Pairs<T>` is an even-length list under the
interpretation you give it, the same way `{ start, durationMs }` is a range. Pick the representation
that makes the bad state unconstructable, then expose the reading you need on top (`pairs.flat()`, a
`rangeEnd()` helper).

## Simplest total type

Don't strengthen everything. Keep `T[]` when every operation on it is total:

```ts
const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0); // [] is 0, fine
```

Strengthen when the loose type forces a lie at a use site. The tells are `!`, `arr[0] as T`, and a
"should never happen" throw:

```ts
// Don't: partiality smuggled past the compiler
function newestSession(sessions: Session[]): Session {
  return sessions.at(0)!; // .at needs lib ES2022 or later
}

// Do: strengthen the input; the assertion disappears
function newestSession(sessions: NonEmpty<Session>): Session {
  return sessions[0];
}
```

Weakening the result to `Session | undefined` is the other total signature. Either way the empty
case lands at the call site, the one place that knows what empty means.

## Return types

Write the type an exported function _promises_, not the widest thing it happens to return. Copying
the inferred union from a hover records an accident, not a contract. A function whose real return
type is an anonymous inline shape has no name for its contract, so give it one; a signature nobody
has written down is usually one nobody has thought about.

```ts
// Don't. The annotation is the inference, copied: an inline shape with no name.
export function summarise(batch: Batch): { id: string; total: number; failed: number } {
  /* ... */
}

// Do. The contract has a name callers and reviewers can find.
export type BatchSummary = { id: string; total: number; failed: number };
export function summarise(batch: Batch): BatchSummary {
  /* ... */
}
```

## `unknown` over `any`

`any` disables type checking for everything it touches. External data is `unknown` until narrowed,
including data a library types as `any`: `JSON.parse` returns it, as does `await response.json()`
under the DOM lib's types (Node's `undici-types` already gives `unknown`). `no-explicit-any` reports
an `any` you write, so it never sees these. Only the `no-unsafe-*` rules of a type-checked
`typescript-eslint` config report using one, and a `recommended` config without them does not. The
[baseline](baseline.md) extends `recommended`, so it reports none of these.

```ts
// Don't. JSON.parse returns any; without the no-unsafe-* rules, nothing reports this access.
function readBar(text: string) {
  const parsed = JSON.parse(text);
  return parsed.foo.bar;
}

// Do. Annotate it unknown; the compiler now makes you narrow.
function readBar(text: string): unknown {
  const parsed: unknown = JSON.parse(text);
  if (typeof parsed !== "object" || parsed === null || !("foo" in parsed)) return undefined;
  const { foo } = parsed; // unknown: narrow again before reading bar
  if (typeof foo !== "object" || foo === null || !("bar" in foo)) return undefined;
  return foo.bar;
}
```

External sources include RPC payloads, `JSON.parse`, `postMessage`, IPC, file contents, environment
variables, database results.

## No `as` casts

Every `as` is a potential runtime crash. Cast only after the type system has verified the claim.

```ts
// Don't
const user = data as User;

// Do. Earn the cast at the boundary.
function parseUser(data: unknown): User {
  if (typeof data !== "object" || data === null) {
    throw new Error("expected object");
  }
  // `in` narrows data, so reading .id needs no cast of its own
  if (!("id" in data) || typeof data.id !== "string") {
    throw new Error("expected id");
  }
  // ... validate all fields
  return data as User; // OK, earned cast after full validation
}
```

When refactoring an `as` out of existing code, identify why TypeScript can't infer:

- Missing discriminant: add one, switch to a discriminated union.
- Overly wide source type (e.g. `Record<string, unknown>`): narrow it.
- Untyped boundary: add a parse function or schema.
- Genuinely inexpressible: use a branded type or `satisfies`.

### The sanctioned casts

Each is here because the compiler _cannot_ express the fact, not because validating was
inconvenient. Each is bounded to a named construct. The first two are the casts this document itself
prescribes; the rest exist because the type cannot be written.

**This list does not generalise.** Resembling an entry is not being one, and "similar to case 5" is
not an argument. If you think you have found another, raise it in review — do not add it inline and
do not widen an existing entry to cover it. A cast that is not on this list is a finding, even if
the surrounding code already contains one.

**1. The last line of a parse function that validated every field it returns.**
`return data as User`, directly below the checks that earn it, as in the example above.

_Does not license:_ a cast anywhere else in that function, or one where the validation is partial.
If you did not check the field, you did not earn it.

**2. A branded-type constructor.** `return input as AgentId` inside `parseAgentId`, directly after
the validation that makes the brand true. The brand is unforgeable by design, so its constructor is
the one place it can be applied.

_Does not license:_ branding a value anywhere other than its constructor.

**3. A caught value narrowed to an error shape.** `catch` binds `unknown` under `strict` (which the
[baseline](baseline.md) sets), and a thrown value can be literally anything, so no amount of
validation turns it into a real type.

```ts
} catch (error) {
  if (axios.isAxiosError(error)) { /* prefer a real guard where one exists */ }
  const e = error as { response?: { status?: number } } | null | undefined;
  const status = e?.response?.status;   // asserted type stays nullable; every access optional
}
```

_Does not license:_ casting a response **body** to a domain type — that is boundary data, so parse
it. Nor casting the caught value to a domain type.

**4. Framework request augmentation.** `(req as AuthenticatedRequest).user`. Middleware attaches the
field; Express's `Request` type cannot follow it.

_Does not license:_ casting `req.body`, `req.query` or `req.params`. Those are untrusted input from
the wire and get parsed like any other boundary.

**5. A library return typed `object`, `any`, or a union it cannot narrow.** `jwt.verify()` returns
`string | object`. The cast records what the library guarantees but does not express.

_Does not license:_ skipping validation of the **contents**. Cast the container, then check each
field you actually rely on.

**6. `as const`, and `import { X as Y }`.** Neither is a type assertion. Listed only so nobody
counts them as one.

Everything else is external data asserted into a domain type, which is the case this rule exists
for:

```ts
localStorage.getItem("theme") as Theme; // holds "purple" after a stale build
e.target.value as JournalTypes; // a <select> yields string
row as T; // a database row is not your model
```

Write the guard.

Existing sites that lack a guard are not a precedent — they are why this rule is written down. Track
them wherever the codebase tracks work, and fix them as you touch them.

## Narrowing hierarchy

From best to last-resort:

1. **Discriminated union switch / if.** Compiler narrows automatically.
1. **`in` operator.** `"key" in obj` narrows to variants containing that key.
1. **`typeof` / `instanceof`.** For primitives and class instances.
1. **User-defined type guard.** When the above aren't enough.
1. **`as` cast.** Only after validation.

```ts
function area(s: Shape): number {
  if ("radius" in s) return Math.PI * s.radius ** 2; // narrowed to circle
  return s.width * s.height; // narrowed to rect
}
```

## Type guards

A guard must actually verify the claim. A lying guard is worse than `as` because the bug hides
behind a name that says it's safe.

```ts
function isCircle(s: Shape): s is Shape & { kind: "circle" } {
  return s.kind === "circle";
}
```

Prefer discriminant narrowing when possible. The guard adds a layer the reader has to follow.

## Exhaustiveness

In default arms, assign the discriminant to a `never`-typed local. The compiler errors if a new
variant is added without handling.

```ts
// Value-returning switch
function area(s: Shape): number {
  switch (s.kind) {
    case "circle":
      return Math.PI * s.radius ** 2;
    case "rect":
      return s.width * s.height;
    default: {
      const _exhaustive: never = s;
      throw new Error(`unhandled variant: ${JSON.stringify(_exhaustive)}`);
    }
  }
}

// Void switch
function handle(s: Shape): void {
  switch (s.kind) {
    case "circle":
      drawCircle(s);
      break;
    case "rect":
      drawRect(s);
      break;
    default: {
      const _exhaustive: never = s;
      void _exhaustive;
    }
  }
}
```

Throw in value-returning switches; `void` in statement switches. Either reads the local, which the
[baseline](baseline.md) needs: its `no-unused-vars` ignores a leading underscore on arguments only,
so an `_exhaustive` that is never read is reported.

`return _exhaustive` is the idiom you will see elsewhere, and it is worse. The compile-time check is
identical, but at runtime it hands the unexpected value back to a caller expecting the return type.
A `kind` that arrives from a third-party payload the union does not cover would make `area()` return
an object where a number was expected, surfacing later as `NaN` in a total rather than at the point
of failure. Throwing keeps the check and fails where the problem is.

## `satisfies` over `as`

`satisfies` checks the value against a type without changing the type of the value. It needs
TypeScript 4.9 or later.

```ts
type Config = { theme: "dark" | "light"; cols: number };

// Don't. The annotation widens: config.theme is now "dark" | "light".
const config = { theme: "dark", cols: 3 } as Config;

// Do. Checked against Config, but config.theme stays "dark".
const config = { theme: "dark", cols: 3 } satisfies Config;
```

What is preserved is the inferred type, which is only narrower where the target property is itself
narrow. Against `{ theme: string }` the inferred type of `config.theme` is `string`, and `satisfies`
gives you nothing extra — it is the literal union in `Config` that does the work. Where the target
is wide and you want the literal anyway, `as const satisfies Config` is the pairing.

## Boundary validation

Validate once where data crosses in; trust types inside. See the
**ad-general:principle-boundary-discipline** principle skill.

- **Third-party REST responses:** read the fields you need and ignore the rest, so a provider adding
  a field does not break you. Reject on a field you require being absent or the wrong type, never on
  a field you did not expect.
- **Persisted JSON:** versioned blob with a try/catch around the parse.
- **Don't re-validate** deep in call chains.

## Schema-derived types

When a `.proto`, OpenAPI spec, GraphQL schema, or database migration already defines a shape, derive
from the generated types instead of duplicating them.

```ts
// Don't. Duplicate shape, drifts when the schema changes.
type CheckSummary = {
  totalCount: number;
  checks: { name: string; status: string }[];
};
function renderChecks(s: CheckSummary) {
  /* ... */
}

// Do. Derive from the generated schema type.
import type { ChecksMessage } from "<generated module>";
function renderChecks(s: Pick<ChecksMessage, "totalCount" | "checks">) {
  /* ... */
}
```

Reach for `Pick`, `Omit`, `Parameters`, `ReturnType`, `Awaited` (TypeScript 4.5 or later), `typeof`
before writing a new interface.

## Earned suppressions

A suppression is a claim that the checker is wrong here. Scope it to the line you are actually
claiming it about, and make the reason true of that line: the gate checks that a reason exists, not
that it holds.

```ts
// Don't. Silences this rule for the rest of the file, including code not yet written.
/* eslint-disable @typescript-eslint/no-explicit-any -- the vendor SDK types its callbacks as any */

// Do. One line, and the next reader learns why.
// eslint-disable-next-line @typescript-eslint/no-explicit-any -- the vendor SDK types this callback as any
```

The first form passes the gate: it names a rule and gives a reason, which is all the
[baseline](baseline.md)'s `no-unlimited-disable` and `require-description` rules ask. It does not
suppress one violation, it suppresses every future one of that rule in that file, and the lint run
stays clean the whole time.

## Real tests

Mock the things you genuinely cannot run — the network, the clock, a paid or destructive API. Run
everything else. A test whose assertions are mostly about its own mocks proves the mocks work.

```ts
// Don't. Asserts that a stub returns what the stub was told to return.
const repo = { get: vi.fn().mockResolvedValue({ id: "1" }) };
expect(await repo.get("1")).toEqual({ id: "1" });

// Do. Mock the boundary, assert the behaviour built on top of it.
exchangeCodeForToken.mockResolvedValue(false);
await authController.handleOAuthCallback(req, res, next);
expect(res.redirectedTo).toBe("/?auth=failed");
```

**Prove a new test can fail.** A test written after the code often passes for the wrong reason, and
a regression test that cannot fail is worse than none because it reads as coverage. Break the
production line it covers, watch the test go red, put it back. If it stays green, the test is not
testing what its name says.

**A `-t` that matches nothing exits 0.** Jest and Vitest both take `-t` to filter by name, and on
both a filter matching nothing reports every test as skipped and exits 0 — check the count, not the
exit code. Where a build excludes tests by file name, a test named outside that convention compiles
into the build output and ships.

**Query the client by role and label, not by test id.** A test id is a hook that exists only for the
test, so it survives a rewrite a user would notice and breaks on one they would not. `getByRole` and
`getByLabelText` fail when the behaviour changes, which is when you want to hear about it. They also
prove what a test id cannot: the element carries the role and accessible name a screen reader will
announce. Testing Library ranks `getByTestId` last, below `getByText` for anything non-interactive.
Reach for it once role, label and text queries have all failed, and say in the test why an
accessible query was impractical.

```ts
// Don't. Passes on a button with no accessible name; breaks when someone renames the test id.
await user.click(screen.getByTestId("submit-btn"));

// Do. Fails if the control stops being a button, loses its name, or is marked `aria-hidden`.
await user.click(screen.getByRole("button", { name: "Submit claim" }));
```

## Structured telemetry

`no-console` is the rule, and a structured logger is the answer wherever one exists. Some surfaces
have none — a browser client typically does — and there `console.error` and `console.warn` are the
fallback that carries a failure to a user or a support conversation. Where the repo's `no-console`
reports them too, as the [baseline](baseline.md)'s `"no-console": "error"` with no `allow` list
does, each call carries `// eslint-disable-next-line no-console -- <why there is no logger here>`.

What does not change is what goes in them:

```ts
// Don't. An axios error carries the serialised request body on error.config.data.
console.error("Authentication failed:", error); // logs the ID token

// Do. Summarise to the fields worth having, and drop the rest.
// eslint-disable-next-line no-console -- browser client, no logger
console.error("Authentication failed:", describeError(error)); // message, code, status
```

Log a summary, never the error object itself, and never a request body, token, credential or account
identifier. Keep one shared helper for this rather than reimplementing it per call site.

## Object args

```ts
// Don't. Four same-typed positionals: swap any two and it still compiles.
openFile(uri, 10, 1, 10, 1);

// Do. Order-independent, self-documenting.
openFile({
  uri,
  selection: {
    startLineNumber: 10,
    startColumn: 1,
    endLineNumber: 10,
    endColumn: 1,
  },
});
```

Skip on hot paths: per-frame render, tokenizers, parsers, anything in a tight loop where the
allocation cost matters.
