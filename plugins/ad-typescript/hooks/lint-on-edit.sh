#!/usr/bin/env bash
# PostToolUse hook: report ESLint findings on the script file Claude just edited. Never fixes.
# Exit 1 is non-blocking and Claude Code shows its stderr; exit 2 feeds the findings back to Claude.
# Not a Node project: stay silent rather than run npx where nothing set ESLint up. Needs no jq.
root=${CLAUDE_PROJECT_DIR:-$PWD}
[ -f "$root/package.json" ] || exit 0
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
  *.ts | *.tsx | *.js | *.jsx | *.mts | *.cts | *.mjs | *.cjs) ;;
  *) exit 0 ;;
esac
if ! command -v jq >/dev/null 2>&1; then
  echo "ad-typescript lint hook: jq is not on PATH, so ESLint did not check the edited file." >&2
  exit 1
fi
# Run npx from the guarded root; a relative path is resolved against the directory we started in.
case "$file" in
  /*) ;;
  *) file=$orig/$file ;;
esac
# ESLint 10 errors on a file outside every config, such as a scratch file in /tmp.
case "$file" in
  "$root"/*) ;;
  *) exit 0 ;;
esac
if ! CDPATH= cd -- "$root"; then
  echo "ad-typescript lint hook: could not enter $root, so ESLint did not check the edited file." >&2
  exit 1
fi
# --no-warn-ignored: ESLint warns on an ignored or unconfigured file, which --max-warnings 0 fails.
out=$(npx --no-install eslint --max-warnings 0 --no-warn-ignored "$file" 2>&1) && exit 0
printf '%s\n' "$out" >&2
exit 2
