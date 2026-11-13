#!/usr/bin/env bash
# PostToolUse hook: report ruff findings on the .py/.pyi file Claude just edited. Never fixes.
# Exit 1 is non-blocking and Claude Code shows its stderr; exit 2 feeds the findings back to Claude.
if ! command -v jq >/dev/null 2>&1; then
  echo "ad-python lint hook: jq is not on PATH, so ruff did not check the edited file." >&2
  exit 1
fi
file=$(jq -r '.tool_input.file_path // empty')
case "$file" in *.py | *.pyi) ;; *) exit 0 ;; esac
# Not a uv project: stay silent rather than let `uv run` create a lockfile and venv.
[ -f "${CLAUDE_PROJECT_DIR:-$PWD}/uv.lock" ] || exit 0
out=$(uv run ruff check --force-exclude --output-format concise "$file" 2>&1) && exit 0
printf '%s\n' "$out" >&2
exit 2
