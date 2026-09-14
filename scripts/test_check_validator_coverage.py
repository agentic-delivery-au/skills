#!/usr/bin/env python3
"""Tests for check_validator_coverage.

Run with: python3 -m unittest discover -s scripts -t scripts

The check exists because an uncovered plugin looks exactly like a covered one
from the outside -- every hook passes either way -- so most of these are about
the shapes that quietly count as coverage and the shapes that must not.
"""

from __future__ import annotations

import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import check_validator_coverage as cvc  # noqa: E402


def config(*paths, hook_id="skill-validator"):
    """A pre-commit config whose skill-validator entries name `paths`."""
    return {
        "repos": [
            {"repo": "https://example.com/other", "hooks": [{"id": "markdownlint"}]},
            {
                "repo": "https://github.com/agent-ecosystem/skill-validator",
                "hooks": [{"id": hook_id, "args": ["check", path]} for path in paths],
            },
        ]
    }


class ConfiguredPathsTests(unittest.TestCase):
    def test_it_finds_the_path_in_a_skill_validator_entry(self):
        self.assertEqual(
            cvc.configured_paths(config("plugins/ad-general/skills/")),
            {"plugins/ad-general/skills"},
        )

    def test_a_platform_specific_id_is_not_coverage(self):
        # Those ids hardcode paths like .claude/skills/, so they validate
        # nothing in this layout even when one names a plugin.
        self.assertEqual(
            cvc.configured_paths(
                config("plugins/ad-general/skills/", hook_id="skill-validator-claude")
            ),
            set(),
        )

    def test_a_path_in_another_hook_is_not_coverage(self):
        other = {
            "repos": [
                {
                    "repo": "local",
                    "hooks": [
                        {
                            "id": "something-else",
                            "files": "^plugins/ad-general/skills/",
                            "args": ["plugins/ad-general/skills/"],
                        }
                    ],
                }
            ]
        }
        self.assertEqual(cvc.configured_paths(other), set())

    def test_a_path_in_a_comment_is_not_coverage(self):
        # Comments do not survive parsing, which is the reason for parsing.
        text = """
repos:
  - repo: https://github.com/agent-ecosystem/skill-validator
    rev: v1.6.1
    hooks:
      # plugins/ad-product/skills/ still needs an entry
      - id: skill-validator
        args: [check, "plugins/ad-general/skills/"]
"""
        self.assertEqual(
            cvc.configured_paths(yaml.safe_load(text)), {"plugins/ad-general/skills"}
        )

    def test_a_leading_dot_slash_names_the_same_directory(self):
        self.assertEqual(
            cvc.configured_paths(config("./plugins/ad-general/skills")),
            {"plugins/ad-general/skills"},
        )

    def test_arguments_that_are_not_skills_directories_are_ignored(self):
        for arg in ("check", "plugins/ad-general", "plugins/ad-general/skills/a-skill"):
            with self.subTest(arg=arg):
                self.assertEqual(cvc.configured_paths(config(arg)), set())

    def test_a_hook_with_no_args_is_not_coverage(self):
        entry = {"repos": [{"repo": "x", "hooks": [{"id": "skill-validator"}]}]}
        self.assertEqual(cvc.configured_paths(entry), set())

    def test_malformed_shapes_do_not_raise(self):
        for broken in (
            None,
            [],
            "text",
            {"repos": "text"},
            {"repos": ["text"]},
            {"repos": [{"hooks": "text"}]},
            {"repos": [{"hooks": ["text"]}]},
            {"repos": [{"hooks": [{"id": "skill-validator", "args": "text"}]}]},
            {"repos": [{"hooks": [{"id": "skill-validator", "args": [None, 7]}]}]},
        ):
            with self.subTest(broken=broken):
                self.assertEqual(cvc.configured_paths(broken), set())


class FindProblemsTests(unittest.TestCase):
    def test_a_covered_directory_has_no_problems(self):
        problems = cvc.find_problems(
            config("plugins/ad-general/skills/"), ["plugins/ad-general/skills"]
        )
        self.assertEqual(problems, [])

    def test_an_uncovered_directory_is_reported(self):
        problems = cvc.find_problems(
            config("plugins/ad-general/skills/"),
            ["plugins/ad-general/skills", "plugins/ad-product/skills"],
        )
        self.assertEqual(len(problems), 1)
        self.assertIn("plugins/ad-product/skills", problems[0])
        self.assertIn("never validated", problems[0])

    def test_an_entry_naming_nothing_is_reported(self):
        problems = cvc.find_problems(
            config("plugins/ad-general/skills/", "plugins/ad-gone/skills/"),
            ["plugins/ad-general/skills"],
        )
        self.assertEqual(len(problems), 1)
        self.assertIn("does not exist", problems[0])

    def test_both_directions_are_reported_together(self):
        problems = cvc.find_problems(
            config("plugins/ad-gone/skills/"), ["plugins/ad-product/skills"]
        )
        self.assertEqual(len(problems), 2)

    def test_a_trailing_slash_on_either_side_still_matches(self):
        problems = cvc.find_problems(
            config("plugins/ad-general/skills"), ["plugins/ad-general/skills/"]
        )
        self.assertEqual(problems, [])

    def test_a_config_that_is_not_an_object_is_reported(self):
        for broken in (None, [], "text"):
            with self.subTest(broken=broken):
                problems = cvc.find_problems(broken, ["plugins/ad-general/skills"])
                self.assertTrue(any("does not hold an object" in p for p in problems))


class MainTests(unittest.TestCase):
    def run_main(self, root):
        """main() reports to stderr, which would otherwise land in hook output
        and read as though this repository had the problem under test."""
        with contextlib.redirect_stderr(io.StringIO()) as captured:
            code = cvc.main(root)
        return code, captured.getvalue()

    def build(self, root, plugins=(), configured=()):
        root = pathlib.Path(root)
        for plugin in plugins:
            (root / "plugins" / plugin / "skills" / "a-skill").mkdir(parents=True)
        (root / cvc.CONFIG).write_text(yaml.safe_dump(config(*configured)), encoding="utf-8")
        return root

    def test_a_covered_tree_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.build(tmp, ["ad-general"], ["plugins/ad-general/skills/"])
            self.assertEqual(self.run_main(tmp)[0], 0)

    def test_an_uncovered_plugin_exits_non_zero(self):
        # The wire between the checks and the exit code: without this,
        # main() could return 0 unconditionally and every other test pass.
        with tempfile.TemporaryDirectory() as tmp:
            self.build(tmp, ["ad-general", "ad-product"], ["plugins/ad-general/skills/"])
            code, reported = self.run_main(tmp)
            self.assertEqual(code, 1)
            self.assertIn("plugins/ad-product/skills", reported)

    def test_a_missing_config_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_main(tmp)[0], 1)

    def test_an_unparseable_config_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            (pathlib.Path(tmp) / cvc.CONFIG).write_text("repos: [unclosed", encoding="utf-8")
            self.assertEqual(self.run_main(tmp)[0], 1)

    def test_a_plugin_without_a_skills_directory_needs_no_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.build(tmp, ["ad-general"], ["plugins/ad-general/skills/"])
            (root / "plugins" / "ad-tools" / "agents").mkdir(parents=True)
            self.assertEqual(self.run_main(tmp)[0], 0)

    def test_a_file_named_skills_is_not_a_directory_to_cover(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.build(tmp, ["ad-general"], ["plugins/ad-general/skills/"])
            (root / "plugins" / "ad-odd").mkdir(parents=True)
            (root / "plugins" / "ad-odd" / "skills").write_text("not a directory")
            self.assertEqual(self.run_main(tmp)[0], 0)

    def test_this_repository_passes(self):
        self.assertEqual(self.run_main(pathlib.Path(__file__).parent.parent)[0], 0)


if __name__ == "__main__":
    unittest.main()
