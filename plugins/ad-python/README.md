# ad-python

Python practices for Agentic Delivery: the `python-best-practices` skill, a pyrefly language server
for Claude, and a hook that reports ruff findings after each edit.

## Install

```sh
/plugin marketplace add agentic-delivery-au/skills
/plugin install ad-python@agentic-delivery
```

## The pyrefly language server

The plugin declares a language server in `.lsp.json` for `.py` and `.pyi` files. It starts pyrefly
with `uv run pyrefly lsp` from the project directory, so it uses whatever pyrefly the project's uv
environment has. Claude gets two things from it:

- **Type diagnostics after each edit.** Claude sees pyrefly's type errors for the file it just
  wrote, without waiting for pre-commit or CI.
- **The `LSP` tool.** Go to definition, find references, type information, symbols and call
  hierarchy, so Claude navigates by the type checker rather than by text search.

Add pyrefly to the project, for example `uv add --dev pyrefly`. Without it the server does not
start. The server runs `uv run` in any project, so in a project with a `pyproject.toml` and no
`uv.lock` it may create `uv.lock` and `.venv`.

Only one language server can handle `.py` files. When two enabled servers claim an extension, the
first registered one wins and the other is not used for it. The official `pyright-lsp` plugin also
claims `.py`, so disable it in Agentic Delivery repos. In the repo's `.claude/settings.json`, set
its entry under `enabledPlugins`. The key is the plugin name and its marketplace, which is
`claude-plugins-official` for the official plugins:

```json
{
  "enabledPlugins": {
    "pyright-lsp@claude-plugins-official": false
  }
}
```

To see which server serves `.py`, and why one is unused, open `/plugin` and read its **Errors** tab.
If the server does not start, `claude --debug` logs the reason.

The language server gives early feedback only. The repo's pre-commit and CI remain the gate.

## The ruff hook

A `PostToolUse` hook on `Write`, `Edit` and `MultiEdit` runs
`uv run ruff check --no-fix --no-fix-only --force-exclude` on each `.py` or `.pyi` file Claude
writes, so files the project's ruff config excludes are skipped. If ruff finds anything, the hook
exits 2 with the findings on stderr, so Claude fixes them in the same turn. It never touches your
source: `--no-fix` and `--no-fix-only` override a `fix = true` or `fix-only = true` in the project's
ruff config, and it runs no `ruff format`. Like any `uv run`, it may update `uv.lock` and create or
update the project's `.venv`.

It needs `jq` and `uv` on your PATH, and ruff in the project, for example `uv add --dev ruff`.
Without it, `uv run` falls back to a ruff on your PATH, whose version and rules may differ from the
gate's, or, with none, Claude sees uv's error after each Python edit instead of findings. The hook
gives early feedback only; the repo's pre-commit and CI remain the gate.

The hook says when it cannot run, and stays out of projects that are not uv projects:

- Only a `uv.lock` at the project root (`$CLAUDE_PROJECT_DIR`, else the current directory) turns the
  hook on, and `uv run` runs from that root. Without one it does nothing and exits 0, whatever the
  file, and needs no `jq`. Such a project is not treated as a uv project, and `uv run` would
  otherwise create a lockfile and a `.venv` there. A monorepo with uv projects only in
  subdirectories gets no lint from this hook.
- In a project with a `uv.lock`, if `jq` is not on your PATH and the edited file is `.py` or `.pyi`,
  it prints one line to stderr and exits 1. That is a non-blocking error, which Claude Code shows,
  so a missing `jq` is not mistaken for a clean file. Other files are skipped silently.
