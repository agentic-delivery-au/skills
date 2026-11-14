#!/usr/bin/env bash
# PostToolUse hook: report ESLint findings on the script file Claude just edited. Never fixes.
# Exit 1 is non-blocking and Claude Code shows its stderr; exit 2 feeds the findings back to Claude.
# Not a Node project: stay silent rather than run npx where nothing set ESLint up. Needs no jq.
# The root is resolved to an absolute physical path (symlinks, a relative path and a trailing slash);
# a root that does not exist is not a project. CDPATH is cleared so cd never searches it.
orig=$PWD
root=$(CDPATH= cd -P -- "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null && pwd -P) || exit 0
[ -f "$root/package.json" ] || exit 0
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
# A file is in the project when its path as given, made absolute, is under the root as given, or
# when its physical path is under the physical root. Either way ESLint gets the logical path, so a
# directory in the project that is a symlink pointing outside it is still linted. A logical path with
# a `..` segment is not trusted, because the prefix test cannot see where it leads.
case "$file" in
  /*) ;;
  *) file=$orig/$file ;;
esac
lroot=${CLAUDE_PROJECT_DIR:-$PWD}
case "$lroot" in
  /*) ;;
  *) lroot=$orig/$lroot ;;
esac
while [ "${lroot%/}" != "$lroot" ]; do lroot=${lroot%/}; done
# The file's directory must exist. ESLint 10 errors on a file outside every config, such as a
# scratch file in /tmp, so that is skipped.
dir=${file%/*}
dir=$(cd -P -- "${dir:-/}" 2>/dev/null && pwd -P) || exit 0
prefix=${root%/}/
lprefix=$lroot/
case "$file/" in
  */../*) logical= ;;
  *) logical=1 ;;
esac
case "${dir%/}/${file##*/}" in
  "$prefix"*) ;;
  *) case "$logical$file" in
       1"$lprefix"*) ;;
       *) exit 0 ;;
     esac ;;
esac
if ! command -v npx >/dev/null 2>&1; then
  echo "ad-typescript lint hook: npx is not on PATH, so ESLint did not check the edited file." >&2
  exit 1
fi
# Run npx from the guarded root.
if ! cd -- "$root"; then
  echo "ad-typescript lint hook: could not enter $root, so ESLint did not check the edited file." >&2
  exit 1
fi
# --no-warn-ignored: ESLint warns on an ignored or unconfigured file, which --max-warnings 0 fails.
out=$(npx --no-install eslint --max-warnings 0 --no-warn-ignored "$file" 2>&1) && exit 0
printf '%s\n' "$out" >&2
exit 2
