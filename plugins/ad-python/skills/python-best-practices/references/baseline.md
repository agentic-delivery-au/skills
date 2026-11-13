# The baseline Ruff and Pyrefly configuration

This is Agentic Delivery's baseline Ruff and Pyrefly configuration, taken from
[`agentic-delivery-au/python-simple-template`](https://github.com/agentic-delivery-au/python-simple-template),
for a project to copy into its `pyproject.toml`. Change the project-specific values (`hello_world`,
the `scripts/` entries, `python-version`, `search-path`) to the project's own and leave the rest.
The decisions in `SKILL.md` and the claims in `toolchain.md` about selected rules, the Pyrefly
preset and test exemptions are claims about this file; a change to the selection or the preset is a
change here.

```toml
[tool.ruff]
line-length = 100
# target-version is inferred from requires-python.
# scripts/ must run on Python 3.10, and Ruff checks the syntax for that.
# The 3.10 bootstrap-repo-tests hook catches 3.11+ stdlib use in the code the tests execute.
per-file-target-version = { "scripts/**" = "py310" }

[tool.ruff.lint]
select = [
  "E", "W",  # pycodestyle
  "F",       # pyflakes
  "I",       # isort
  "B",       # bugbear
  "C4",      # comprehensions
  "UP",      # pyupgrade
  "N",       # pep8-naming
  "D",       # pydocstyle
  "ANN",     # annotations
  "S",       # bandit (security)
  "G",       # flake8-logging-format
  "ARG",     # unused arguments
  "RUF",     # ruff-specific
  "TD003",   # a todo with no issue link
  "BLE",     # blind `except Exception` (broad except clauses)
]
ignore = [
  "D417",    # Args/Returns/Raises sections not required when the signature is self-explanatory
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["D100", "D101", "D102", "D103", "S101", "ANN"]
"scripts/test_*.py" = ["D100", "D101", "D102", "D103", "S101", "ANN"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.isort]
# The package is installed into .venv, so without this Ruff sorts it with the
# third-party imports.
known-first-party = ["hello_world"]

[tool.ruff.format]
quote-style = "double"

[tool.pyrefly]
python-version = "3.14"
preset = "strict"
# No project-excludes: the hook names the paths to check; see README.
# search-path: scripts for the tests' bootstrap_repo import, src because naming it drops the root.
search-path = ["src", "scripts"]

# Leave empty and the preset decides. Add an entry only to record a deliberate
# exception, and say why.
[tool.pyrefly.errors]
```

The template's `.pre-commit-config.yaml` runs the gate through uv with the lockfile pinned:
`uv run --locked ruff check --force-exclude --fix`, `uv run --locked ruff format --force-exclude`
and `uv run --locked pyrefly check src scripts`. Pyrefly is given the paths, so `tests/` is outside
its gate.
