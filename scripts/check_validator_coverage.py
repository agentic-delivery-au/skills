#!/usr/bin/env python3
"""Fail when a plugin's skills are not covered by a skill-validator entry.

skill-validator discovers one level down, so an entry points at a directory
whose children are skills and covers that plugin alone. A plugin with no entry
is simply never validated and every hook stays green -- which has already
happened once here, when a plugin was added while the hook was being introduced.

The skills on disk are the source of truth rather than the marketplace listing:
an unlisted plugin's SKILL.md is still committed to this repository, and still
worth validating.
"""

from __future__ import annotations

import pathlib
import re
import sys

import yaml

CONFIG = pathlib.Path(".pre-commit-config.yaml")
# Only the generic id counts. The platform-specific ids (skill-validator-claude
# and its siblings) hardcode paths such as .claude/skills/ that match nothing in
# this layout, so a directory covered only by one of those is genuinely
# uncovered rather than a gap in this check.
HOOK_ID = "skill-validator"
SKILLS_PATH = re.compile(r"plugins/[^/]+/skills")


def normalise(path: str) -> str:
    """`./plugins/x/skills/` and `plugins/x/skills` are the same directory."""
    return pathlib.PurePosixPath(path).as_posix().rstrip("/")


def items(value: object) -> list:
    """A list to iterate, whatever the config actually holds there."""
    return value if isinstance(value, list) else []


def configured_paths(config: object) -> set[str]:
    """The skills directories named in a skill-validator hook's args.

    A path in a comment, or in another hook's `files:` regex, is not coverage,
    so the config is parsed rather than scanned.
    """
    if not isinstance(config, dict):
        return set()
    paths = set()
    for repo in items(config.get("repos")):
        if not isinstance(repo, dict):
            continue
        for hook in items(repo.get("hooks")):
            if not isinstance(hook, dict) or hook.get("id") != HOOK_ID:
                continue
            for arg in items(hook.get("args")):
                if isinstance(arg, str) and SKILLS_PATH.fullmatch(normalise(arg)):
                    paths.add(normalise(arg))
    return paths


def find_problems(config: object, skill_dirs: list[str]) -> list[str]:
    if not isinstance(config, dict):
        return [f"{CONFIG} does not hold an object, so no hook is configured at all"]
    configured = configured_paths(config)
    present = {normalise(d) for d in skill_dirs}
    problems = [
        f"{directory} has no skill-validator entry, so its skills are never validated"
        for directory in sorted(present - configured)
    ]
    problems += [
        f"a skill-validator entry names {directory}, which does not exist"
        for directory in sorted(configured - present)
    ]
    return problems


def skills_directories(root: pathlib.Path) -> list[str]:
    return sorted(
        p.relative_to(root).as_posix() for p in root.glob("plugins/*/skills") if p.is_dir()
    )


def main(root: str | None = None) -> int:
    base = pathlib.Path(root or ".")
    path = base / CONFIG
    if not path.is_file():
        print(f"error: {CONFIG} is missing", file=sys.stderr)
        return 1
    try:
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError, UnicodeDecodeError) as err:
        print(f"error: {CONFIG} could not be read: {err}", file=sys.stderr)
        return 1

    problems = find_problems(config, skills_directories(base))
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"\nAdd or correct a skill-validator entry in {CONFIG}.", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
