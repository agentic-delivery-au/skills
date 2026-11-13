# Python patterns

Examples for the rules in `SKILL.md`. Every snippet is written the way this skill wants it:
annotated, double-quoted, one-line docstrings.

## Docstrings that say something

With annotations required, an `Args` section repeats the signature. One line describing behaviour
tells a reader something the code does not.

```python
# Yes
def fetch_records(table_name: str, limit: int = 100) -> list[dict[str, object]]:
    """Return up to `limit` rows from `table_name`, newest first."""
    ...


# No: sections that restate types the signature already carries.
def fetch_records(table_name: str, limit: int = 100) -> list[dict[str, object]]:
    """Fetch records.

    Args:
        table_name: The table name.
        limit: The limit.
    """
```

Write the sections where they carry something the signature cannot: a `Raises:` for an exception a
caller has to handle, or a `Returns:` explaining what an opaque value means.

## No `__future__` import

New projects target 3.14 or later, where deferred annotation evaluation (PEP 649) makes forward
references work unquoted. The `from __future__ import annotations` import is no longer needed, and
it switches every annotation in the module back to a string (PEP 563). No Ruff rule reports it.

```python
# Yes: the bare name works, though `Node` is not yet defined inside its own class.
class Node:
    """One node of a tree."""

    def parent(self) -> Node | None:
        """Return the node above this one, or None at the root."""


# No: an import 3.14 made unnecessary.
from __future__ import annotations
```

## Logging

Do not log a token, a credential, a request body or a personal identifier. Log the fields worth
having.

## TODO

```python
# Yes
# TODO: https://github.com/agentic-delivery-au/myrepo/issues/42

# No: the baseline's `TD003` passes both, because each carries a link.
# TODO: https://github.com/agentic-delivery-au/myrepo/issues/42 handle the retry case
# TODO(alice): https://github.com/agentic-delivery-au/myrepo/issues/42
```

The description belongs in the issue, where it can be tracked and closed. The
[baseline](baseline.md)'s `TD003` checks that a link is present, not that nothing follows it.

## Suppressions

Put the suppression on the line, name the rule code, and say why.

```python
# Yes
def handle(payload) -> None:  # noqa: ANN001  # pyrefly: ignore[implicit-any-parameter]
    """Process one webhook payload."""


# No: a bare noqa silences whatever else that line trips, now and later.
def handle(payload) -> None:  # noqa
    """Process one webhook payload."""
```

Pyrefly has its own directive and its own error kinds, so a Ruff code in it suppresses nothing:

```python
def load_config() -> Config:
    """Return the application configuration."""
    return _legacy_loader()  # pyrefly: ignore[bad-return]  # legacy API, no stubs
```

A file-level `# ruff: noqa: UP035` is the one to avoid hardest. It silences today's violation and
every future violation of that rule in that file, including in code nobody has written yet, so one
fix that was awkward once buys a permanent blind spot. Several suppressions clustered in one area
are a signal to fix the underlying problem.

## Unused arguments

`ARG` usually wants a rename, not a suppression. Ruff's default `dummy-variable-rgx` matches an
underscore-prefixed name, so the rule stops reporting and the name says the parameter is ignored on
purpose.

```python
# Yes: the caller passes a URL, this stub has no use for it.
def _fake_fetch(_url: str, timeout: int) -> dict[str, object]:
    """Return a canned payload recording the timeout the caller asked for."""
    return {"timeout": timeout}


# No: a suppression where a rename would do.
def _fake_fetch(url: str, timeout: int) -> dict[str, object]:  # noqa: ARG001  # stub ignores it
    """Return a canned payload recording the timeout the caller asked for."""
    return {"timeout": timeout}
```

If no caller supplies the argument at all, delete it. Two cases need neither: `ARG002` already skips
a method decorated with `@typing.override`, because the checker enforces that signature; and a
pytest fixture requested only for its side effect cannot be renamed, because pytest resolves
fixtures by parameter name, so move it to `@pytest.mark.usefixtures("name")` and drop the parameter.

## Imports

Import the module, not the name inside it. The exemption is `typing`, `collections.abc` and
`typing_extensions`.

```python
# Yes: `Sequence` is the exemption; `repository` is imported as a module.
from collections.abc import Sequence

from myproject.grants import repository


def recent(ids: Sequence[repository.GrantId]) -> list[repository.Grant]:
    """Return the grants named by `ids`, in the order given."""
    return [repository.find(grant_id) for grant_id in ids]


# No: the call site no longer says where `find` came from, and a second module
# with a `find` collides with it.
from myproject.grants.repository import find


def recent(ids: Sequence[GrantId]) -> list[Grant]:
    """Return the grants named by `ids`, in the order given."""
    return [find(grant_id) for grant_id in ids]
```

Ruff's import sorting (`I`) finds the project's own package through its `src` directories.
`known-first-party` in `pyproject.toml`, which the [baseline](baseline.md) sets, is for a package
that lookup misses, such as one installed into `.venv`: without it that package sorts with the
third-party imports, and nothing reports it.

## Exceptions

Name what you expect, keep the `try` body to the call that can raise, and chain the cause.

```python
# Yes
try:
    payload = client.get_grant(grant_id)
except httpx.HTTPStatusError as e:
    raise GrantUnavailableError(f"grant {grant_id} could not be fetched") from e
record = parse_grant(payload)


# No: a KeyError raised by parse_grant is reported as an unavailable grant, and the
# chaining is only incidental — __cause__ is unset, so nothing records that the HTTP
# failure caused this one.
try:
    payload = client.get_grant(grant_id)
    record = parse_grant(payload)
except Exception:
    raise GrantUnavailableError(f"grant {grant_id} could not be fetched")
```

`raise X from None` is legitimate where the cause would leak an internal detail or a credential, but
it is a decision: carry whatever the caller needs into the new message first.

## Illegal states unrepresentable

Model variants as a tagged union of frozen dataclasses and match on the type. A single class with a
status string and a field per outcome lets contradictions construct.

```python
# No: status="failed" with rows=[] and error=None all type-check.
@dataclasses.dataclass
class LoadResult:
    status: str
    rows: list[Row] | None = None
    error: str | None = None


# Yes: every constructible value is a state that can really happen.
@dataclasses.dataclass(frozen=True)
class Loaded:
    """A completed load and the rows it returned."""

    rows: tuple[Row, ...]


@dataclasses.dataclass(frozen=True)
class Failed:
    """A load that did not complete, and why."""

    error: str


LoadResult = Loaded | Failed
```

`frozen=True` because a result nobody can rebind after the fact is one fewer place a state changes
behind a caller's back. It is shallow: it stops `result.rows = []`, not `result.rows.append(row)`,
so a field that must stay put is a `tuple` rather than a `list`.

## Exhaustive matching

Put `assert_never` in the fallthrough arm. Add a third variant to `LoadResult` and the checker
points at every match that does not handle it, before anything runs.

```python
def describe(result: LoadResult) -> str:
    """Return a one-line summary of a load result."""
    match result:
        case Loaded(rows):
            return f"loaded {len(rows)} rows"
        case Failed(error):
            return f"failed: {error}"
        case _:
            typing.assert_never(result)
```

`assert_never` raises if it is ever reached, which is what you want when a value arrives from
outside the union the code was written against. Its real work is at check time.

## Brand semantic primitives

`NewType` costs nothing at runtime and stops two identifiers of the same underlying type being
swapped.

```python
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

GrantId = typing.NewType("GrantId", str)
DonorId = typing.NewType("DonorId", str)


def parse_grant_id(raw: str) -> GrantId:
    """Return `raw` as a GrantId, rejecting anything that is not a UUID."""
    if not _UUID.fullmatch(raw):
        raise ValueError(f"not a grant id: {raw}")
    return GrantId(raw)


def link(grant: GrantId, donor: DonorId) -> None:
    """Attach a donor to a grant."""
```

Validate once in the parse function. `link(donor, grant)` is now a type error rather than a support
ticket.

## Parse at the boundary

External data is `object` until a parse function turns it into a declared type. `Any` is the one to
avoid: it disables checking for everything it touches, transitively.

```python
def parse_grant(payload: object) -> Grant:
    """Return a Grant from an API payload, rejecting anything missing or mistyped."""
    if not isinstance(payload, dict):
        raise ValueError("expected a JSON object")
    raw_id = payload.get("id")
    if not isinstance(raw_id, str):
        raise ValueError("grant id missing or not a string")
    amount = payload.get("amount_cents")
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise ValueError("amount_cents missing or not an integer")
    return Grant(id=parse_grant_id(raw_id), amount_cents=amount)
```

Read the fields you need and ignore the rest, so a provider adding a field does not break you.
Reject on a field you require being absent or the wrong type, never on one you did not expect.

`bool` subclasses `int`, so `isinstance(amount, bool)` has to be rejected first or JSON `true`
arrives as an amount of 1. The same trap catches any numeric field parsed straight off a payload.

The boundaries are HTTP responses, `json.loads`, database rows, `os.environ`, CLI arguments, files
on disk and message payloads. Past the parse, trust the type: re-validating deep in a call chain is
noise that also tells the next reader the boundary cannot be trusted.

`typing.cast` is a claim the checker cannot verify, so it belongs on the last line of a parse
function that has checked every field it returns, and nowhere else. A `cast` over unvalidated data
is the same crash as no annotation at all, with the traceback moved somewhere less useful.

## Tests

Testing doctrine is the **ad-general:test-driven-development** skill's: what a test is for and what
you may mock. This section gives the pytest spelling, and the traps that are Python's alone. Its
snippets follow the `tests/` exemption that `references/toolchain.md` records, so they carry no
annotations and no docstrings on test modules, classes, methods or functions (the baseline exempts
`D100` to `D103`), and they use `assert`.

### Patch the binding the code reaches

`mock.patch` imports the module its string names and replaces an attribute on it, so the target has
to be the namespace the code under test reads at call time. The import rule does most of that work
for you: a module that does `import httpx` and calls `httpx.get` looks the attribute up on `httpx`
every call, so `mock.patch("myproject.grants.client.httpx.get")` and `mock.patch("httpx.get")` are
the same patch. It leaves one gap: a binding the module made once, when it was imported.

```python
# client.py opens one pool at import: _client = httpx.Client(base_url=_BASE_URL)

# Yes: replace the object the module holds, so nothing leaves the process.
with mock.patch.object(client, "_client") as http:
    http.get.return_value = httpx.Response(200, json={"id": _GRANT_ID, "amount_cents": 500})
    assert client.get_grant(_GRANT_ID).amount_cents == 500


# No: `_client` was built at import, so patching the factory rebinds nothing the
# module reaches and the real request goes out. Here that fails somewhere
# confusing; where the call is a side effect nothing asserts on — a webhook, a
# write — it passes, and the side effect really happened.
with mock.patch("httpx.Client") as client_cls:
    client_cls.return_value.get.return_value = httpx.Response(200, json={"id": _GRANT_ID})
    assert client.get_grant(_GRANT_ID).amount_cents == 500
```

The other form is a name bound into the module under test by `from httpx import get`, which you
patch as `myproject.grants.client.get`. The import rule bans that spelling in our own code; code you
do not own still writes it, so read the module before choosing a target. `mock.patch.object` takes
the module you already imported rather than a string, which keeps the target beside the thing it
names.

The example patches the HTTP client, not one of your own modules. This section covers where to point
a patch; the doctrine decides whether you may patch the target at all.

### `pytest.raises` needs `match=`

Any `ValueError` in the block satisfies a bare `pytest.raises(ValueError)`, including one the test's
own arrangement raised by mistake. The test then reports green without reaching the behaviour it
names.

```python
# Yes: pinned to the rejection this test is about, with only the call that
# raises inside the block.
grant = parse_grant(_PAYLOAD)
with pytest.raises(ValueError, match="unknown donor"):
    link(grant.id, _UNKNOWN_DONOR)


# No: parse_grant rejects the trimmed fixture with its own ValueError, which
# satisfies the block on its own — `link` is never called and the test passes.
with pytest.raises(ValueError):
    grant = parse_grant(_PARTIAL_PAYLOAD)
    link(grant.id, _UNKNOWN_DONOR)
```

Pin the words that tell this error from every other one, not the whole sentence: the
`ad-general:test-driven-development` skill's `references/writing-good-tests.md` counts exact message
wording as a change detector, and a `match=` carrying the full message fails on a reword that broke
nothing. It is a regex searched against the message, so keep the fragment clear of metacharacters or
wrap it in `re.escape`. Keep the block down to the call that raises, for the reason you keep a `try`
body short.

### `parametrize` is the table-driven shape

The `ad-general:test-driven-development` skill's `references/writing-good-tests.md` asks for
table-driven tests with literal `want` values. You write that in pytest with
`@pytest.mark.parametrize`: one row per case, each `want` worked out by hand, and every case running
whatever the ones before it did.

```python
# Yes
@pytest.mark.parametrize(
    ("result", "want"),
    [
        (Loaded(()), "loaded 0 rows"),
        (Loaded((_ROW, _ROW)), "loaded 2 rows"),
        (Failed("timeout"), "failed: timeout"),
    ],
    ids=["empty-load", "two-rows", "failure-carries-the-reason"],
)
def test_describe_summarises_a_load_result(result, want):
    assert describe(result) == want


# No: one test that stops at the first failing case, so the cases after it never
# run, and the report names the function rather than the case that broke.
def test_describe():
    for result, want in ((Loaded(()), "loaded 0 rows"), (Failed("timeout"), "failed: timeout")):
        assert describe(result) == want
```

Write `ids=`, so a failure reports `test_describe_summarises_a_load_result[two-rows]`. pytest falls
back to `result0` and `result1` for anything that is not a string, a number or a bool, which names a
position rather than a case. One behaviour per table: where a case needs its own arrangement or a
different assertion, the branch it forces into the body costs more than a second test.
