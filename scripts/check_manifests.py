#!/usr/bin/env python3
"""Fail on marketplace problems that make a plugin fail to install.

Structure and consistency are checked together here rather than split between a
JSON schema and a script. The published SchemaStore schema was the obvious
alternative and is not used: it is fetched unversioned over the network, so it
fails an offline commit and can turn CI red without a commit, and it is already
behind the format -- it rejects the bare-name sources that metadata.pluginRoot
exists to enable.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

MARKETPLACE = pathlib.Path(".claude-plugin/marketplace.json")
# Claude Code accepts other forms, but the claude.ai marketplace sync rejects
# them, and nothing local says so until a plugin silently fails to appear.
KEBAB = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
# semver.org's own expression, so a prerelease with leading zeros is caught.
SEMVER = re.compile(
    r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
    r"(?:-(?:(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?:[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
)
# Claude Desktop's managed sync drops a marketplace named any of these.
RESERVED = {"org", "org-provisioned", "unknown"}


def check_name(label: str, name: object) -> list[str]:
    if not isinstance(name, str) or not name:
        return [f"{label} has no name"]
    # fullmatch, not match: a trailing newline is a name the sync rejects.
    return [] if KEBAB.fullmatch(name) else [f'{label} "{name}" is not kebab-case']


def check(marketplace: object, load_plugin) -> list[str]:
    """`load_plugin` takes a source path and returns that plugin's plugin.json.

    It raises FileNotFoundError when the directory or the manifest is missing,
    and ValueError when the manifest will not parse.
    """
    if not isinstance(marketplace, dict):
        return ["marketplace.json does not hold an object"]

    problems = check_name("marketplace", marketplace.get("name"))
    if str(marketplace.get("name", "")).lower() in RESERVED:
        problems.append(f'marketplace "{marketplace["name"]}" is a reserved name')
    if not isinstance(marketplace.get("owner"), dict):
        problems.append("marketplace has no owner object")

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        return problems + ["marketplace has no plugins list"]

    # A bare name is resolved against this, so the two have to be read together.
    root = (marketplace.get("metadata") or {}).get("pluginRoot")
    seen: set[str] = set()

    for index, entry in enumerate(plugins):
        if not isinstance(entry, dict):
            problems.append(f"plugin entry {index} is not an object")
            continue

        name = entry.get("name")
        label = f'plugin "{name}"' if isinstance(name, str) and name else f"plugin entry {index}"
        problems += check_name(label, name)
        if isinstance(name, str):
            if name in seen:
                problems.append(f'{label} is listed twice; plugin names have to be unique')
            seen.add(name)

        source = entry.get("source")
        if source is None:
            problems.append(f"{label} has no source")
            continue
        if not isinstance(source, str):
            # An object source is fetched from elsewhere by the consumer, so
            # there is nothing on disk here to resolve.
            continue
        if ".." in pathlib.PurePosixPath(source).parts:
            problems.append(f'{label}: source "{source}" contains "..", which the format forbids')
            continue

        path = source if source.startswith("./") else None
        if path is None:
            if not isinstance(root, str):
                problems.append(
                    f'{label}: source "{source}" is neither a ./ path nor a name under '
                    "metadata.pluginRoot"
                )
                continue
            path = f"{root.rstrip('/')}/{source}"

        try:
            plugin = load_plugin(path)
        except FileNotFoundError as err:
            problems.append(f"{label}: {err}")
            continue
        except ValueError as err:
            problems.append(f"{label}: {path} has an unreadable plugin.json: {err}")
            continue

        if plugin.get("name") != name:
            problems.append(
                f'{label}: plugin.json calls it "{plugin.get("name")}", '
                "so the two manifests disagree"
            )
        version = plugin.get("version")
        if version is None:
            problems.append(f"{label}: plugin.json has no version, so nothing can bump it")
        elif not isinstance(version, str) or not SEMVER.fullmatch(version):
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
