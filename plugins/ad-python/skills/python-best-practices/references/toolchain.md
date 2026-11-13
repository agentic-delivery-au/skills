# Running the gate

Commands, and what their output has to say before you claim a check passed.

## Find the project's gate before you run anything

Read `pyproject.toml` for `[tool.ruff]` and `[tool.pyrefly]`, `.github/workflows/` for what CI runs,
and `.pre-commit-config.yaml` for what runs locally. Run those, through the runner the project uses
— `uv run …` where there is a `uv.lock`, otherwise whatever the workflow invokes. The `ad-python`
lint hook follows the same rule: it runs only where a `uv.lock` exists.

Do not create a `ruff.toml`, `.ruff.toml` or `setup.cfg`: configuration belongs in `pyproject.toml`
and nowhere else. Do not pass `--select`, `--ignore` or `--config` to change which rules run,
because then you have checked something other than what CI will check. The baseline configuration is
in [baseline.md](baseline.md) and nowhere in this file; the project's `pyproject.toml` is the source
of truth for what the project actually runs.

A project with no `[tool.ruff]` at all is not configured yet. Set it up from
[baseline.md](baseline.md) as its own change, rather than half-configuring it inside an unrelated
one.

## The three checks

| Command                        | Passing evidence                    | Failing evidence                                                                                           |
| ------------------------------ | ----------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `uv run ruff format --check .` | `N files already formatted`, exit 0 | `unformatted: File would be reformatted` with a diff per file, then `N files would be reformatted`, exit 1 |
| `uv run ruff check .`          | `All checks passed!`, exit 0        | A block per finding, then `Found N errors.`, exit 1                                                        |
| `uv run pyrefly check`         | `INFO 0 errors`, exit 0             | `ERROR <message> [error-kind]` per finding, then `INFO N errors`, exit 1                                   |

Run Pyrefly with the paths the project's gate passes. The gate in
`agentic-delivery-au/python-simple-template` is `uv run --locked pyrefly check src scripts`. A bare
`pyrefly check` also checks `tests/`, which that gate does not, so errors there are not the gate's.

- **A formatting failure is fixed by running the formatter**, never by hand-editing whitespace to
  guess what it wanted. `ruff format` writes the files; re-run `--check` for the evidence.
- **`ruff check --fix` writes its fixes and still exits non-zero** for everything it could not fix.
  The first run is not the verdict. Stage the fixes and run again; the `All checks passed!` from the
  second run is the evidence.
- **Piping hides the exit code.** `uv run pyrefly check | tail` reports `tail`'s status, not
  Pyrefly's. Quote the `INFO N errors` line, which cannot be faked by a pipe.

For triage, `ruff check . --statistics` prints a count per rule, which tells you whether you are
looking at one mistake repeated or twenty different ones. `--output-format concise` gives one
`path:line:col: CODE message` per finding, which is the form to paste into a pull request.

## Ruff passing is not Pyrefly passing

The two tools see different things, which is why this skill requires both. A class whose signature
is fully annotated can still leave an attribute for the checker to infer:

```python
def __init__(self, base_url: str) -> None:
    """Store the base URL and start unauthenticated."""
    self.base_url: str = base_url
    self.token = None
```

Ruff reports nothing here. Pyrefly reports, against the `self.token = None` line:

```text
ERROR This expression is implicitly inferred to be `Any | None`. Please provide an explicit type annotation. [implicit-any-attribute]
```

"`ruff check` passed" is never evidence that the types are right.

The bracketed kind at the end of a Pyrefly error is what goes inside `# pyrefly: ignore[...]`. A
Ruff code there suppresses nothing, and vice versa.

## What the gate does not catch

Measured against the [baseline](baseline.md)'s Ruff rule selection; re-check after upgrading Ruff.
These rules are real, and the gate either misses them entirely or catches only part of them, so each
needs its own probe. Where a rule covers part of the ground, the probe below looks for the residue
it leaves, not for the whole rule:

Each probe covers stubs as well as modules, so each carries both `--include` flags. Do not lift them
into a shell variable: the quotes survive the expansion, the globs stop matching, and the probe
returns nothing, which reads exactly like a clean result.

- **A TODO that links an issue and then says more.** The baseline selects `TD003`, so a TODO with no
  link fails the build. It asks only whether a link is present, so `# TODO(alice): <url>` and
  `# TODO: <url> and a description` both satisfy it and both break the rule, which wants the URL and
  nothing else.
  `grep -rnE "#\s*TODO" --include='*.py' --include='*.pyi' . | grep -vE "#\s*TODO: https://\S+$"`
  keeps the lines that are anything other than a bare issue URL, which is exactly the residue
  `TD003` leaves. Match `#\s*TODO` rather than bare `TODO`, or prose in a docstring that happens to
  say TODO comes back as a finding. Excluding on `issues/` instead would hide
  `# TODO: <url> and a description`, which is half of what is left to find.
- **A broad `except Exception` that keeps the traceback.** The baseline selects `BLE`, so a handler
  that discards the traceback fails the build. `BLE001` exempts a re-raise, a
  `logger.exception(...)` call and `logger.error(..., exc_info=True)`, and cannot judge whether an
  exempt handler is genuinely a re-raise or a deliberate isolation point — the only two the Google
  guide permits. A handler that logs with `.exception()` and carries on regardless is still a
  violation and the gate is silent on it.
  `grep -rn "except Exception" --include='*.py' --include='*.pyi' .` lists every candidate; read
  each and keep the ones that neither re-raise nor sit at a boundary.
- **Importing names rather than modules.** `from x import some_function` is not reported.
  `grep -rnE "^\s*from " --include='*.py' --include='*.pyi' .` lists candidates, not findings: the
  two forms are syntactically identical, so read each one and keep those importing a name. Match
  every `from` line rather than a narrower pattern, or `from package import Class` and relative
  `from . import x` lines slip past. Allow the leading whitespace too, or you miss every import
  deferred inside a function or an `if TYPE_CHECKING:` block. Discard the `typing`,
  `collections.abc` and `typing_extensions` hits, which are the exemption.
- **An unneeded `from __future__ import annotations`.** No rule reports it on 3.14, and it turns
  every annotation in the module back into a string (PEP 563).
  `grep -rn "^from __future__ import" --include='*.py' --include='*.pyi' .` — read each hit and
  remove `annotations` from it, deleting the line if it was the only feature, in a new project. A
  hit can name several features, as in `from __future__ import division, annotations`, which is why
  the probe does not match on `annotations`. It stays anchored to column 0 on purpose: an indented
  future statement is a `SyntaxError`, so anchoring misses nothing.

If one of these keeps coming back, the answer is a rule, not a reminder: see the
**ad-general:principle-encode-lessons-in-structure** principle skill. Selecting extra rules on top
of the configured set is explicitly allowed. Removing one to make existing code pass is not.

## Exhaustiveness is something the checker proves

`typing.assert_never` in the fallthrough arm turns a new variant into a failed check rather than a
runtime surprise. Add a third member to a union that two `case` arms cover and Pyrefly reports
`Argument ... is not assignable to parameter arg with type Never in function typing.assert_never [bad-argument-type]`,
pointing at the match that was not updated. That error, not a passing test suite, is the evidence
the union is handled everywhere.

## Adopting Pyrefly on a codebase that has never run it

The first run of a codebase that has never been type-checked fails with enough errors that somebody
switches the check off. Do not start at `strict`.

Use a baseline so CI is green immediately, then delete entries as you fix them rather than
regenerating the file — a regenerated baseline hides the new debt among the old. Where the debt
should be visible in review instead, `pyrefly suppress` writes inline `# pyrefly: ignore[...]`
comments you can see in a diff.

`check-unannotated-defs`, `infer-return-types` and `preset = "legacy"` loosen the checking itself.
All three are migration states, not settings: record in the project README which are set and what
has to be true before each comes out. The evidence that adoption is progressing is the baseline
shrinking, not CI staying green.

## Untyped dependencies

Find real types before suppressing anything. Many packages ship a `py.typed` marker, many others
have a `types-` stub package on PyPI, and `pyrefly stubgen` generates stubs from source. A stub
fixes the problem for everyone who depends on the package; `Any` only hides it.

Where there genuinely are none, `ignore-missing-imports` and `replace-imports-with-any` replace the
import. Name the modules you mean and give a reason in a comment. A wildcard turns the checker off
for everything it matches, which is the whole project more often than the author expected.

## Where enforcement actually lives

CI is the enforcement point: a lint job runs the three checks on every pull request and blocks merge
on failure. Add them to the pipeline the project already has rather than adopting a new workflow
file wholesale.

Pre-commit hooks run the same checks earlier, and are convenience rather than enforcement — a local
hook can be skipped with `git commit --no-verify` and can run against a stale config. Pyrefly needs
`pass_filenames: false` in a hook, because a file that type checks on its own can still break its
callers. If the full run gets slow enough that people reach for `--no-verify`, move Pyrefly to
`pre-push`; do not drop it.

## Tests

Testing doctrine is the **ad-general:test-driven-development** skill's, not this one's. Tests are
checked differently: the baseline exempts `tests/**` (and `scripts/test_*.py`) from `ANN`, from the
missing-docstring rules `D100` to `D103` (module, class, method and function), and from `S101`, so
tests may use `assert`. The other docstring rules still apply to them.
`agentic-delivery-au/python-simple-template`'s gate runs `pyrefly check src scripts`, so it does not
type-check `tests/**`, though it does check `scripts/test_*.py`. The Pyrefly language server still
reports errors on a `tests/` file you edit; those are not the gate's, so do not annotate tests just
to silence them. A green run over a test file therefore proves less than a green run over a source
file, so do not cite one as evidence about the other.

`references/patterns.md` § Tests carries the pytest probes for that doctrine: where to point a
patch, what `pytest.raises` has to pin, and the table-driven shape.
