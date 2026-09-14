#!/usr/bin/env python3
"""Fail on marketplace problems a JSON schema cannot express.

The published schemas check structure: required keys, types, valid JSON. They
cannot say whether a plugin's source resolves to a real plugin, whether the two
manifests agree on its name, or whether a name is one the claude.ai marketplace
sync will reject. Those are the ones that break an install rather than a parse.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

MARKETPLACE = pathlib.Path(".claude-plugin/marketplace.json")
# Claude Code accepts other forms, but the claude.ai marketplace sync rejects
# them, and nothing local says so until a plugin silently fails to appear.
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESERVED = {"org", "org-provisioned", "unknown"}
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


def check_name(label: str, name: object) -> list[str]:
    if not isinstance(name, str) or not name:
        return [f"{label} has no name"]
    problems = []
    if not KEBAB.match(name):
        problems.append(f'{label} "{name}" is not kebab-case')
    if name.lower() in RESERVED:
        problems.append(f'{label} "{name}" is a reserved name')
    return problems


def check(marketplace: dict, load_plugin) -> list[str]:
    """`load_plugin` takes a relative source path and returns its plugin.json.

    It raises FileNotFoundError when the directory or the manifest is missing,
    and ValueError when the manifest will not parse.
    """
    problems = check_name("marketplace", marketplace.get("name"))

    for entry in marketplace.get("plugins") or []:
        name = entry.get("name")
        label = f'plugin "{name}"' if name else "a plugin entry"
        problems += check_name(label, name)

        source = entry.get("source")
        if not isinstance(source, str) or not source.startswith("./"):
            # A remote source is fetched by the consumer, so there is nothing
            # here to resolve; the schema has already checked its shape.
            continue

        try:
            plugin = load_plugin(source)
        except FileNotFoundError as err:
            problems.append(f"{label}: {err}")
            continue
        except ValueError as err:
            problems.append(f"{label}: {source} has an unreadable plugin.json: {err}")
            continue

        if plugin.get("name") != name:
            problems.append(
                f'{label}: plugin.json calls it "{plugin.get("name")}", '
                "so the two manifests disagree"
            )
        version = plugin.get("version")
        if version is None:
            problems.append(f"{label}: plugin.json has no version, so nothing can bump it")
        elif not isinstance(version, str) or not SEMVER.match(version):
            problems.append(f'{label}: version "{version}" is not semver')

    return problems


def filesystem_loader(root: pathlib.Path):
    def load(source: str) -> dict:
        directory = root / source
        if not directory.is_dir():
            raise FileNotFoundError(f"{source} is not a directory")
        manifest = directory / ".claude-plugin" / "plugin.json"
        if not manifest.is_file():
            raise FileNotFoundError(f"{source} has no .claude-plugin/plugin.json")
        try:
            return json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            raise ValueError(str(err)) from err

    return load


def main(root: str | None = None) -> int:
    base = pathlib.Path(root or ".")
    path = base / MARKETPLACE
    if not path.is_file():
        print(f"error: {MARKETPLACE} is missing", file=sys.stderr)
        return 1
    try:
        marketplace = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        print(f"error: {MARKETPLACE} will not parse: {err}", file=sys.stderr)
        return 1

    problems = check(marketplace, filesystem_loader(base))
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
