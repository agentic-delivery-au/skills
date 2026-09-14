#!/usr/bin/env python3
"""Tests for check_manifests.

Run with: python3 -m unittest discover -s scripts -t scripts

The checks here exist because the published schemas cannot express them, so the
tests are mostly about the cases a schema would wave through.
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import check_manifests as cm  # noqa: E402


def marketplace(**overrides):
    base = {
        "name": "agentic-delivery",
        "owner": {"name": "Agentic Delivery"},
        "plugins": [{"name": "ad-general", "source": "./plugins/ad-general"}],
    }
    base.update(overrides)
    return base


def loader(plugins):
    """A stand-in for the filesystem: maps source path to its plugin.json."""

    def load(source):
        if source not in plugins:
            raise FileNotFoundError(f"{source} is not a directory")
        value = plugins[source]
        if isinstance(value, Exception):
            raise value
        return value

    return load


GOOD = {"./plugins/ad-general": {"name": "ad-general", "version": "0.0.0"}}


class CheckTests(unittest.TestCase):
    def test_a_consistent_marketplace_has_no_problems(self):
        self.assertEqual(cm.check(marketplace(), loader(GOOD)), [])

    def test_source_pointing_nowhere_is_reported(self):
        # The case that matters most: the official validator skips every
        # plugin-level check and exits 0 when a source does not resolve.
        problems = cm.check(marketplace(), loader({}))
        self.assertEqual(len(problems), 1)
        self.assertIn("not a directory", problems[0])

    def test_directory_without_a_manifest_is_reported(self):
        def missing_manifest(source):
            raise FileNotFoundError(f"{source} has no .claude-plugin/plugin.json")

        problems = cm.check(marketplace(), missing_manifest)
        self.assertIn("no .claude-plugin/plugin.json", problems[0])

    def test_unparseable_manifest_is_reported(self):
        problems = cm.check(marketplace(), loader({"./plugins/ad-general": ValueError("bad json")}))
        self.assertIn("unreadable plugin.json", problems[0])

    def test_names_disagreeing_between_manifests_is_reported(self):
        plugins = {"./plugins/ad-general": {"name": "something-else", "version": "1.0.0"}}
        problems = cm.check(marketplace(), loader(plugins))
        self.assertIn("disagree", problems[0])

    def test_missing_version_is_reported(self):
        plugins = {"./plugins/ad-general": {"name": "ad-general"}}
        problems = cm.check(marketplace(), loader(plugins))
        self.assertIn("no version", problems[0])

    def test_non_semver_version_is_reported(self):
        plugins = {"./plugins/ad-general": {"name": "ad-general", "version": "v1"}}
        problems = cm.check(marketplace(), loader(plugins))
        self.assertIn("not semver", problems[0])

    def test_leading_zeroes_and_empty_identifiers_are_not_semver(self):
        for version in ("01.2.3", "1.2.3-01", "1.2.3-", "1.2", "v1.2.3", "1.2.3\n"):
            plugins = {"./plugins/ad-general": {"name": "ad-general", "version": version}}
            with self.subTest(version=version):
                problems = cm.check(marketplace(), loader(plugins))
                self.assertTrue(any("not semver" in p for p in problems))

    def test_semver_prerelease_and_build_are_accepted(self):
        for version in ("1.2.3", "1.2.3-rc.1", "1.2.3+build.5", "0.0.0", "1.2.3-alpha.1+b.2"):
            plugins = {"./plugins/ad-general": {"name": "ad-general", "version": version}}
            with self.subTest(version=version):
                self.assertEqual(cm.check(marketplace(), loader(plugins)), [])

    def test_non_kebab_entry_name_is_reported(self):
        # The official validator checks this on plugin.json but not on the
        # marketplace entry, so a mixed-case entry name reaches the sync.
        mp = marketplace(plugins=[{"name": "AD_General", "source": "./plugins/ad-general"}])
        problems = cm.check(mp, loader(GOOD))
        self.assertTrue(any("kebab-case" in p for p in problems))

    def test_reserved_marketplace_names_are_reported(self):
        for name in ("org", "org-provisioned", "unknown"):
            with self.subTest(name=name):
                problems = cm.check(marketplace(name=name), loader(GOOD))
                self.assertTrue(any("reserved" in p for p in problems))

    def test_a_plugin_may_use_a_name_reserved_only_for_marketplaces(self):
        # The rule is Claude Desktop's, and it applies to the marketplace name.
        mp = marketplace(plugins=[{"name": "unknown", "source": "./plugins/unknown"}])
        plugins = {"./plugins/unknown": {"name": "unknown", "version": "1.0.0"}}
        self.assertEqual(cm.check(mp, loader(plugins)), [])

    def test_duplicate_plugin_names_are_reported(self):
        mp = marketplace(
            plugins=[
                {"name": "ad-general", "source": "./plugins/ad-general"},
                {"name": "ad-general", "source": "./plugins/ad-general"},
            ]
        )
        problems = cm.check(mp, loader(GOOD))
        self.assertTrue(any("listed twice" in p for p in problems))

    def test_parent_traversal_in_a_source_is_reported(self):
        mp = marketplace(
            plugins=[{"name": "ad-general", "source": "./plugins/../plugins/ad-general"}]
        )
        problems = cm.check(mp, loader({"./plugins/../plugins/ad-general": GOOD["./plugins/ad-general"]}))
        self.assertTrue(any('".."' in p for p in problems))

    def test_a_bare_name_resolves_through_plugin_root(self):
        mp = marketplace(
            metadata={"pluginRoot": "./plugins"},
            plugins=[{"name": "ad-general", "source": "ad-general"}],
        )
        self.assertEqual(cm.check(mp, loader(GOOD)), [])

    def test_a_bare_name_without_a_plugin_root_is_reported(self):
        mp = marketplace(plugins=[{"name": "ad-general", "source": "ad-general"}])
        problems = cm.check(mp, loader(GOOD))
        self.assertTrue(any("pluginRoot" in p for p in problems))

    def test_a_dangling_bare_name_is_still_resolved(self):
        mp = marketplace(
            metadata={"pluginRoot": "./plugins"},
            plugins=[{"name": "ad-typo", "source": "ad-typo"}],
        )
        problems = cm.check(mp, loader(GOOD))
        self.assertTrue(any("not a directory" in p for p in problems))

    def test_a_trailing_newline_in_a_name_is_reported(self):
        mp = marketplace(plugins=[{"name": "ad-general\n", "source": "./plugins/ad-general"}])
        problems = cm.check(mp, loader(GOOD))
        self.assertTrue(any("kebab-case" in p for p in problems))

    def test_structure_problems_are_reported_not_raised(self):
        for broken in ("not an object", ["a", "list"], 7):
            with self.subTest(broken=broken):
                self.assertTrue(cm.check(broken, loader(GOOD)))
        self.assertTrue(cm.check(marketplace(plugins="nope"), loader(GOOD)))
        self.assertTrue(cm.check(marketplace(plugins=["nope"]), loader(GOOD)))
        self.assertTrue(cm.check(marketplace(plugins=[None]), loader(GOOD)))
        self.assertTrue(cm.check(marketplace(owner="nope"), loader(GOOD)))

    def test_a_missing_source_is_reported(self):
        mp = marketplace(plugins=[{"name": "ad-general"}])
        problems = cm.check(mp, loader(GOOD))
        self.assertTrue(any("no source" in p for p in problems))

    def test_remote_sources_are_not_resolved_but_still_named(self):
        mp = marketplace(
            plugins=[{"name": "Third_Party", "source": {"source": "github", "repo": "a/b"}}]
        )
        problems = cm.check(mp, loader({}))
        self.assertEqual(len(problems), 1)
        self.assertIn("kebab-case", problems[0])

    def test_every_plugin_is_checked_not_just_the_first(self):
        mp = marketplace(
            plugins=[
                {"name": "ad-general", "source": "./plugins/ad-general"},
                {"name": "ad-second", "source": "./plugins/ad-second"},
            ]
        )
        problems = cm.check(mp, loader(GOOD))
        self.assertTrue(any("ad-second" in p for p in problems))


class MainTests(unittest.TestCase):
    def test_missing_marketplace_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(cm.main(tmp), 1)

    def test_unparseable_marketplace_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / cm.MARKETPLACE
            path.parent.mkdir(parents=True)
            path.write_text("{not json", encoding="utf-8")
            self.assertEqual(cm.main(tmp), 1)

    def test_a_real_tree_on_disk_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / ".claude-plugin").mkdir(parents=True)
            (root / ".claude-plugin" / "marketplace.json").write_text(
                json.dumps(marketplace()), encoding="utf-8"
            )
            plugin = root / "plugins" / "ad-general" / ".claude-plugin"
            plugin.mkdir(parents=True)
            (plugin / "plugin.json").write_text(
                json.dumps({"name": "ad-general", "version": "0.0.0"}), encoding="utf-8"
            )
            self.assertEqual(cm.main(tmp), 0)

    def test_a_tree_with_a_problem_exits_non_zero(self):
        # Without this, main() could return 0 unconditionally and every other
        # test would still pass -- the wire from check() to the exit code is
        # the only thing that makes this a hook rather than a library.
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / ".claude-plugin").mkdir(parents=True)
            (root / ".claude-plugin" / "marketplace.json").write_text(
                json.dumps(marketplace()), encoding="utf-8"
            )  # the plugin directory is deliberately absent
            self.assertEqual(cm.main(tmp), 1)

    def test_this_repository_passes(self):
        self.assertEqual(cm.main(pathlib.Path(__file__).parent.parent), 0)


if __name__ == "__main__":
    unittest.main()
