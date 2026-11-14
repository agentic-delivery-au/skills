#!/usr/bin/env bash
# PostToolUse hook: report ruff findings on the .py/.pyi file Claude just edited. Never fixes.
# Exit 1 is non-blocking and Claude Code shows its stderr; exit 2 feeds the findings back to Claude.
# Not a uv project: stay silent rather than let `uv run` create a lockfile and venv. Needs no jq.
root=${CLAUDE_PROJECT_DIR:-$PWD}
[ -f "$root/uv.lock" ] || exit 0
orig=$PWD
IFS= read -r -d '' input || true
if command -v jq >/dev/null 2>&1; then
  file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
else
  # Without jq, pull file_path out of the JSON by pattern, only to decide the extension.
  file=
  pattern='"file_path"[[:space:]]*:[[:space:]]*"((\\.|[^"\\])*)"'
  [[ $input =~ $pattern ]] && file=${BASH_REMATCH[1]}
fi
case "$file" in
  *.py | *.pyi) ;;
  *) exit 0 ;;
esac
if ! command -v jq >/dev/null 2>&1; then
  echo "ad-python lint hook: jq is not on PATH, so ruff did not check the edited file." >&2
  exit 1
fi
# Run uv from the guarded root; a relative path is resolved against the directory we started in.
case "$file" in
  /*) ;;
  *) file=$orig/$file ;;
esac
if ! CDPATH= cd -- "$root"; then
  echo "ad-python lint hook: could not enter $root, so ruff did not check the edited file." >&2
  exit 1
fi
out=$(uv run ruff check --no-fix --force-exclude --output-format concise "$file" 2>&1) && exit 0
printf '%s\n' "$out" >&2
exit 2
