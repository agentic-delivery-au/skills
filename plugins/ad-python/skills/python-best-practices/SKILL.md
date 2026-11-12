---
name: python-best-practices
description: "Python practices for Agentic Delivery: the decisions table, then the Google style guide, then PEP 8. Use when reading or editing any .py or .pyi file, when changing a project's pyproject.toml or its Ruff or Pyrefly configuration, and when reading a Ruff or Pyrefly failure."
---

# Python best practices

Three sources, most authoritative first. Where two disagree, the higher one wins outright.

1. The decisions in "What Agentic Delivery decides" below. This is what a pull request is reviewed
   against and what the project's Ruff and Pyrefly configuration enforces.
1. The [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html). The declared
   base: the decisions table is a list of deviations from Google, not from PEP 8.
1. [PEP 8](https://peps.python.org/pep-0008/). The substrate both rest on, and the shared vocabulary
   a reader already has. Use it where the other two are silent.

Apply the **ad-general:principle-type-system-discipline** and
**ad-general:principle-boundary-discipline** principle skills first; this skill grounds them in
Python syntax. Testing doctrine is the **ad-general:test-driven-development** skill's;
`references/patterns.md` § Tests carries the pytest probes that express it, and
`references/toolchain.md` records how the checks differ under `tests/`.

Run the project's own gate first and do not re-derive by eye anything it checks.
`references/toolchain.md` gives the commands, the output each has to produce, and the short list of
rules no gate enforces.

The pyrefly language server and the ruff hook that `ad-python` ships report type errors and lint
findings after each edit. That is early feedback: pre-commit and CI remain the gate. A quiet hook is
not a passing gate: both check only the edited file, the hook does not run `ruff format --check`,
and the gate runs Pyrefly over its whole scope, not only the edited file.

## What Agentic Delivery decides

| Rule               | What the base says                                                 | What Agentic Delivery requires                                                                                                                                                                                                                                 |
| ------------------ | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Python version     | —                                                                  | 3.14 or later for new projects, declared once as `requires-python`, from which Ruff infers `target-version` so the two cannot drift. `match` where it aids clarity.                                                                                            |
| Forward references | Google: `from __future__ import annotations`, or a quoted name.    | No `from __future__ import annotations`. PEP 649 deferred evaluation ships in 3.14, so the bare name works, and the import switches every annotation in the module back to a string (PEP 563). No Ruff rule reports the import; `UP037` reports a quoted name. |
| Docstring shape    | Google: Args, Returns and Raises sections on anything non-trivial. | One line describing behaviour, where the signature explains itself. Annotations already state the types an Args block would repeat.                                                                                                                            |
| TODO               | Google: `TODO`, a colon, a link, then a description.               | The issue URL and nothing else. Description and context belong in the issue, where someone can close them. The gate checks that a link is present, not that nothing follows it.                                                                                |
| Toolchain          | Google: pylint, Black or Pyink, pytype.                            | Ruff for lint and format, Pyrefly for types, pinned as dev dependencies, configured in `pyproject.toml` and nowhere else. Do not add flake8, isort, Black, mypy or pylint; each overlaps or conflicts with the two above.                                      |
| Suppressions       | —                                                                  | Name the code and say why: `# noqa: ANN001  # signature fixed by the SDK`. A bare `# noqa` or a file-level `# ruff: noqa` hides every future violation too. Pyrefly's own form is `# pyrefly: ignore[bad-return]`, carrying a Pyrefly error kind.              |
| Unused arguments   | —                                                                  | Rename to `_name` rather than suppress `ARG`: Ruff's `dummy-variable-rgx` matches it and the name says the parameter is ignored on purpose. Delete it if no caller passes it. For a pytest fixture wanted only for its side effect, use `usefixtures`.         |
| `staticmethod`     | Google: never, unless a library API forces it.                     | No restriction. Google's reason is large-scale dependency injection, which does not apply at this size.                                                                                                                                                        |

Never drop a selected Ruff rule, loosen the Pyrefly preset, turn off a Pyrefly error kind such as
the `implicit-any` family, or widen an exclude to make existing code pass. Changing any of those is
a change to these decisions, so argue for it in a pull request against this skill rather than
quietly in a project config. Selecting extra rules on top is fine.

## The base, where an agent's default is wrong

| Rule                        | Summary                                                                                                                                                                                            | Source           |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| Import modules, not names   | `from x import y` is for modules and packages, not for individual classes or functions. `typing`, `collections.abc` and `typing_extensions` are the exemption.                                     | Google           |
| Narrow the `except`         | Name the exception you expect. Catching `Exception` is for re-raising or a deliberate isolation point. Keep the `try` body down to the call that can raise.                                        | Google           |
| Chain the cause             | `from None` discards the original traceback and is a decision you make on purpose; carry the detail you are dropping into the new message.                                                         | PEP 8            |
| `is` for singletons         | Test `is not None` rather than truthiness wherever `0`, `""` or `[]` is a legitimate value.                                                                                                        | Google           |
| Truthiness for sequences    | `if not items:`, not `if len(items) == 0:`. Never compare a boolean to `True` or `False` with `is`; `E712` reports the `==` form.                                                                  | PEP 8            |
| Naming                      | No type in the name (`id_to_name_dict`). Module constants are `UPPER_SNAKE_CASE` and type variables `CapWords`; Ruff's `N816` reports only a mixedCase module-level variable, not a lowercase one. | Google           |
| `self` and `cls`            | Leave them unannotated. No Ruff rule reports an annotated one.                                                                                                                                     | Google           |
| Single-character names      | Only counters and iterators (`i`, `j`, `k`, `v`), `e` for a caught exception, `f` for a file handle, and private type variables (`_T`, `_P`).                                                      | PEP 8 and Google |
| Public surface              | One leading underscore marks internal; list a module's public names in `__all__`. Two leading underscores are name mangling to dodge a subclass clash, not privacy, so reach for one underscore.   | PEP 8 and Google |
| Close what you open         | A `with` block releases the file, socket, lock or connection on the exception path too. Never rely on a destructor; `contextlib.closing` covers an object with no context manager.                 | Google           |
| Comprehension complexity    | One `for` clause and at most one filter. Past that, write the loop.                                                                                                                                | Google           |
| Function length             | Past roughly 40 lines, ask what can come out. Not a hard limit and no linter enforces it.                                                                                                          | Google           |
| `if __name__ == "__main__"` | A module that can be imported must not run its main program on import.                                                                                                                             | Google           |

## Grounding the type-system principles

From the principle skills, in Python syntax.

| Pattern                        | In Python                                                                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Illegal states unrepresentable | A tagged union of frozen dataclasses, matched with `match`. Not one class carrying a `status` string and four optionals, which lets contradictory combinations construct.  |
| Brand semantic primitives      | `NewType("OrderId", str)`. Validate once in a parse function, trust the type after.                                                                                        |
| Exhaustive matching            | `typing.assert_never(x)` in the `case _:` arm, so Pyrefly fails when a variant is added and this match is not updated.                                                     |
| `object` over `Any`            | `Any` disables checking everywhere it reaches. Untrusted input is `object`, narrowed before use.                                                                           |
| Earned `cast`                  | `typing.cast` is an assertion the checker cannot verify, so it belongs on the last line of a parse function that checked every field it returns, and nowhere else.         |
| Parse at the boundary          | HTTP payloads, JSON, database rows, environment variables and CLI arguments are untyped until a parse function turns them into a declared type. Do not re-validate inside. |
| Strengthen only where partial  | Keep the plain `list[T]` while every operation on it is total. Tighten the type only where the loose one forces a `cast`, an `assert` or a "cannot happen" raise.          |

Examples: `references/patterns.md`. Commands, and the output each has to produce:
`references/toolchain.md`.
