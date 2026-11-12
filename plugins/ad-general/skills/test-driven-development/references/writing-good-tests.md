# Writing Good Tests

**Load this reference when:** writing or changing tests, adding mocks, or adding cleanup/helper
methods for tests.

## Overview

A test exists to catch a specific break. Two principles govern everything here:

```text
1. Every test names the break it catches
2. Every test exercises the real thing
```

Strict TDD produces both naturally: a test written first and watched failing against real code has
already proven it can fail, and only earns a mock when the real dependency proves slow or external.

## Principle 1: Name the Break

Before writing the test body, answer: **what production change should make this test fail — and is
that change a bug or a decision?** A test earns its place by catching a wrong branch, missing side
effect, wrong argument, boundary case, or broken contract.

**Name the test so its failure report reads as a sentence.** That report is where the name is read —
in a list of failures, by someone who has not opened the file.
`test_retries_a_failed_call_three_times` tells them what the system stopped doing; `test_retry`
sends them to the source to find out. Read the failure report aloud: if it is not a sentence about
the system, the name is not finished.

**Derive expectations independently.** Use literals and hand-checked fixtures; table-driven tests
with literal `want` values are the preferred shape. An expectation computed by the code under test —
or its helpers — passes no matter what that code does:

```typescript
// ❌ Mirror assertion: the same builder computes both sides — always true
const expected = buildSearchQuery({ tag: "urgent" });
expect(buildSearchQuery({ tag: "urgent" })).toBe(expected);

// ✅ Hand-derived literal
expect(buildSearchQuery({ tag: "urgent" })).toBe('tag:"urgent"');
```

**No change detectors.** If only intentional decisions can fail a test — a constant's value, exact
message wording, private structure — it fires on redesign and sleeps through bugs. Test the
behaviour that depends on the decision: not `expect(MAX_RETRIES).toBe(5)` but "a failing call is
retried 5 times and the 6th attempt never happens."

**Behaviour, not text.** Asserting that a script, skill, or config contains an exact line proves
only that the source is the source. Run scripts against controlled inputs and assert outputs, side
effects, or exit codes. Documents that instruct agents are tested by the consuming agent's
behaviour; prose for humans earns no test at all.

**Your code, not the framework.** Test the contract your code makes at its boundaries — the route
you register, the query you emit, the payload you produce. Upstream mechanics are their maintainers'
tests to write (the classic: asserting your router invokes a registered handler — that is the
framework's test, not yours). When upstream behaviour genuinely surprised you, write one narrow
characterisation test naming the assumption. The same boundary applies inside your code:
constructors, getters, constants, and trivial forwarding earn tests only when they validate,
normalise, default, derive, enforce, branch, or cause side effects — otherwise assert the first
consumer-visible result that depends on them.

### Gate function: naming the break

```text
BEFORE writing the test body:
  Name the production change that would make this test fail.

  Cannot name one            → redesign around an observable behaviour
  "The source text changed"  → run the artifact and assert its effects
  Only intentional decisions → change detector; test the behaviour
                               that depends on the decision

  Confirm the expected value is derived without the code under test.
  IF it reuses the code's logic or helpers:
    Replace it with a literal or hand-checked fixture

  Read the failure report this name will produce, aloud.
  Not a sentence about the system → rename before writing the body
```

## Principle 2: Exercise the Real Thing

**The mock's presence earns no assertion.** An assertion that the mock exists, or returns what you
configured, passes when the mock is present and fails when it is absent — it says nothing about the
component. What the component sends to the mock is different: see "Make doubles specific" below.
Assert the real component's behaviour; if the mock is what you are checking, unmock it or delete the
assertion.

```typescript
// ✅ Real behaviour
expect(screen.getByRole("navigation")).toBeInTheDocument();

// ❌ Mock existence
expect(screen.getByTestId("sidebar-mock")).toBeInTheDocument();
```

**your human partner's correction:** "Are we testing the behaviour of a mock?"

**Mock at the right level.** Learn every side effect of the real method before replacing it; mock
the slow or external operation and keep what the test depends on real. When unsure, run the test
against the real implementation first and observe what actually needs to happen.

```typescript
// ❌ The mock swallows the config write that duplicate detection reads
vi.mock("ToolCatalog", () => ({
  discoverAndCacheTools: vi.fn().mockResolvedValue(undefined),
}));

// ✅ Mock only the slow server startup; the config write stays real
vi.mock("MCPServerManager");
```

**Mock at the system boundary, never between your own modules.** The boundary is set by what the
code does, not by who wrote it: a module of yours that launches a process, opens a socket or reads
the clock sits on it, which is why `MCPServerManager` above is fair game — the gate below lists the
rest. A module that only computes sits inside it. Mock it only where it is genuinely slow, and then
only the slow part: a mock across an internal seam otherwise proves the seam exists rather than that
the behaviour is right, staying green while either side is wrong, until both sides have drifted and
only the mock still agrees with them.

**Make doubles specific.** When arguments, call counts, or ordering are part of the contract, assert
them — a fake that accepts anything verifies nothing. Give each branch (success, error, malformed)
its own fixture or spy, so the wrong branch cannot satisfy the expectation.

**Mirror real data completely.** Mock the complete structure as it exists in reality — all
documented fields — not just the ones your test reads. Partial mocks fail silently when downstream
code reads an omitted field: the test passes while integration breaks.

**Production classes carry production methods only.** Cleanup that only tests need lives in test
utilities, never as a `destroy()` on the production class. Ask: is this method called only from
tests? Does this class own this resource's lifecycle? Wrong answers → test utility.

**Prefer real components over complex mocks.** When mock setup outgrows the test logic, mocks miss
methods the real components have, or tests break when the mock changes, switch to an integration
test with real components. **your human partner's question:** "Do we need to be using a mock here?"

### Gate function: exercising the real thing

```text
BEFORE adding a mock or test helper:
  List the real method's side effects; keep the ones the test
  depends on real — mock the slow/external level below them.

  Does the target leave your system — process, socket, network,
  clock, filesystem, paid or destructive API?
    Yes → mock only the part that leaves; keep the side effects
          the test reads real
    No, and it is not slow → internal seam; use the real module

  Mock responses mirror the complete real structure.

  A method only tests call lives in test utilities, not production.

  About to assert that the mock exists, or returns what you configured?
    Unmock it or delete the assertion.
```

## Tests Ship With the Implementation

The TDD cycle — failing test, minimal implementation, refactor — is what "complete" means. Ship the
tests the behaviour needs and only those: trivial code and human prose earn none, and a test written
to satisfy process costs maintenance forever.

## The Mutation Check

Before finishing, think through the realistic mutations of the production code; at least one test
should fail for each:

- Wrong constant or argument
- Wrong branch handler
- Missing state change or side effect
- Empty or default return
- Missing validation for zero, empty, nil, unauthorised, or malformed input

A mutation nothing catches marks the behaviour as unprotected — or the test as tautological.

A mutation you only imagine is not evidence. Where you rely on one as proof, as with a
characterisation test that passes first time, run it: break the production code temporarily, watch
the test fail, then restore the code by undoing your own edit only.

## Quick Reference

| When you...                        | Do                                                          |
| ---------------------------------- | ----------------------------------------------------------- |
| Write any test                     | Name the break it catches — a bug, not a decision           |
| Write the test's name              | Make its failure report read as a sentence                  |
| Build an expected value            | Derive it by hand; never with the code under test           |
| Test a script or document          | Run it / pressure-test its consumer; never grep its text    |
| Reach for a dependency test        | Test your boundary contract, not their documented mechanics |
| Want to assert on a mocked element | Test the real component, or unmock it                       |
| Are about to mock a method         | Learn its side effects; mock the slow/external level        |
| Want to mock a module you own      | Only if it leaves your system or is genuinely slow          |
| Build a mock response              | Mirror the real structure completely                        |
| Need cleanup only tests use        | Put it in test utilities                                    |
| Watch mock setup balloon           | Switch to an integration test with real components          |
| Finish a test file                 | Run the mutation check                                      |

## Warning Signs

- Setup and assertion share the same object, guaranteeing equality
- The test can fail only through a panic, crash, or missing selector
- The test fails on every intentional change, never on accidental breakage
- Expected values are hidden behind loops, builders, or helpers
- The test greps source text, or asserts a removed symbol stays removed
- The test would still matter if only the framework remained
- The test exists for coverage, checking no side effect or outcome
- An assertion checks a `*-mock` test ID, or that the mock exists or returns what you configured
- A mock stands between two modules you own, and the mocked one is neither slow nor leaves your
  system
- A test name needs the file open to be understood
- A method is called only from test files
- Mock setup is more than half the test, or you can't explain why the mock is needed
- Mocking "just to be safe"
