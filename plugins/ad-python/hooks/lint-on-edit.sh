#!/usr/bin/env bash
# PostToolUse hook: report ruff findings on the .py/.pyi file Claude just edited. Never fixes.
file=$(jq -r '.tool_input.file_path // empty')
case "$file" in *.py | *.pyi) ;; *) exit 0 ;; esac
out=$(uv run ruff check --force-exclude --output-format concise "$file" 2>&1) && exit 0
printf '%s\n' "$out" >&2
exit 2
