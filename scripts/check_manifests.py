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
ABSENT = object()


def local_path(source: object, plugin_root: object) -> str | None:
    """The repo-relative directory a source points at, or None if it is remote.

    Shared by both checks: when only one of them understood bare names, a repo
    using metadata.pluginRoot lost the other's cover with no signal.
    """
    if not isinstance(source, str):
        return None
    if source.startswith("./"):
        relative = source[2:]
    elif isinstance(plugin_root, str):
        relative = f"{plugin_root.rstrip('/')}/{source}"
        relative = relative[2:] if relative.startswith("./") else relative
    else:
        return None
    return pathlib.PurePosixPath(relative).as_posix().rstrip("/") or None


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
    metadata = marketplace.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        problems.append("marketplace metadata is not an object")
        metadata = None
    root = (metadata or {}).get("pluginRoot")
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
        if isinstance(source, dict):
            # An object source is fetched from elsewhere by the consumer, so
            # there is nothing on disk here to resolve.
            continue
        if not isinstance(source, str):
            problems.append(f'{label}: source "{source}" is neither a path nor an object')
            continue
        if ".." in pathlib.PurePosixPath(source).parts:
            problems.append(f'{label}: source "{source}" contains "..", which the format forbids')
            continue

        path = local_path(source, root)
        if path is None:
            problems.append(
                f'{label}: source "{source}" is neither a ./ path nor a name under '
                "metadata.pluginRoot"
            )
            continue

        try:
            plugin = load_plugin(path)
        except FileNotFoundError as err:
            problems.append(f"{label}: {err}")
            continue
        except ValueError as err:
            problems.append(f"{label}: {path} has an unreadable plugin.json: {err}")
            continue

        if not isinstance(plugin, dict):
            problems.append(f"{label}: {path}'s plugin.json does not hold an object")
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


def check_release_coverage(marketplace: object, config: object, manifest: object) -> list[str]:
    """Every plugin needs a release-please package entry, and a correct one.

    A missing entry means the plugin never releases. An entry without the right
    extra-files means it releases while the version a consumer reads never
    moves, and one without a component means two plugins fight over one tag.
    """
    if not isinstance(marketplace, dict) or not isinstance(config, dict):
        return []
    packages = config.get("packages")
    if not isinstance(packages, dict):
        return ["release-please-config.json has no packages object"]
    versions = manifest if isinstance(manifest, dict) else {}

    problems = []
    root = (marketplace.get("metadata") or {}).get("pluginRoot")
    expected = set()

    for entry in marketplace.get("plugins") or []:
        if not isinstance(entry, dict):
            continue
        path = local_path(entry.get("source"), root)
        if path is None:
            continue
        expected.add(path)
        label = f'plugin "{entry.get("name")}"'

        package = packages.get(path)
        if package is None:
            problems.append(
                f"{label}: {path} has no release-please package entry, so it never releases"
            )
        else:
            problems += check_package(label, path, package)

        # get() cannot tell an absent key from one holding null, and the two
        # are different mistakes.
        version = versions.get(path, ABSENT)
        if version is ABSENT:
            problems.append(f"{label}: {path} is missing from .release-please-manifest.json")
        elif not isinstance(version, str):
            problems.append(f"{label}: its .release-please-manifest.json version is not a string")

    for path in sorted(set(packages) - expected):
        problems.append(
            f"release-please releases {path}, which is not a plugin in the marketplace"
        )
    return problems


def check_package(label: str, path: str, package: object) -> list[str]:
    if not isinstance(package, dict):
        return [f"{label}: its release-please package entry is not an object"]
    problems = []
    # Without a component both packages tag the same name and collide.
    if not package.get("component"):
        problems.append(f"{label}: its release-please package entry has no component")
    wanted = ".claude-plugin/plugin.json"
    files = package.get("extra-files")
    files = files if isinstance(files, list) else []
    if not any(
        isinstance(f, dict)
        and str(f.get("path", "")).endswith(wanted)
        and f.get("jsonpath") == "$.version"
        for f in files
    ):
        problems.append(
            f"{label}: nothing in its extra-files bumps {wanted}, so the published version "
            "would never move"
        )
    return problems


def read_json(path: pathlib.Path) -> object | None:
    """None when the file is absent; a parse or read failure is the caller's."""
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


READ_ERRORS = (json.JSONDecodeError, OSError, UnicodeDecodeError)


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
    # Skipped when the repo does not use release-please at all.
    try:
        config = read_json(base / "release-please-config.json")
        release_manifest = read_json(base / ".release-please-manifest.json")
    except READ_ERRORS as err:
        problems.append(f"a release-please file could not be read: {err}")
    else:
        if config is not None:
            problems += check_release_coverage(marketplace, config, release_manifest)
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
