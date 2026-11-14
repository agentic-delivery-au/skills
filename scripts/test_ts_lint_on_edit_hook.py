#!/usr/bin/env python3
"""Tests for ad-typescript's lint-on-edit PostToolUse hook, with a fake `npx` first on PATH.

Run with: python3 -m unittest discover -s scripts -t scripts
"""

import json
import pathlib
import shutil
import stat
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins" / "ad-typescript" / "hooks" / "lint-on-edit.sh"
HOOKS_JSON = ROOT / "plugins" / "ad-typescript" / "hooks" / "hooks.json"

FAKE_NPX = r"""#!/usr/bin/env bash
printf '%s\n' "$*" >>"$STUB_LOG"
pwd >"$STUB_LOG.pwd"
[ -z "${STUB_FINDINGS:-}" ] && exit 0
echo "${!#}"
echo "  1:8  error  'os' is defined but never used  @typescript-eslint/no-unused-vars"
exit 1
"""

BASH, JQ = shutil.which("bash"), shutil.which("jq")
DIRNAME, BASENAME = shutil.which("dirname"), shutil.which("basename")


@unittest.skipUnless(BASH and JQ and DIRNAME and BASENAME, "needs bash, jq, dirname and basename")
class TsLintOnEditTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = pathlib.Path(self._tmp.name)
        self.bin = self.make_bin(self.tmp / "bin", with_jq=True)
        self.log = self.tmp / "npx.log"
        self.project = self.tmp / "project"
        self.project.mkdir()
        (self.project / "package.json").write_text("{}", encoding="utf-8")

    @staticmethod
    def make_bin(bin_dir, *, with_jq, with_npx=True):
        """A PATH holding only what the hook uses, the fake npx, and jq if asked."""
        bin_dir.mkdir()
        for name, target in (("bash", BASH), ("dirname", DIRNAME), ("basename", BASENAME)):
            (bin_dir / name).symlink_to(target)
        if with_jq:
            (bin_dir / "jq").symlink_to(JQ)
        if with_npx:
            npx = bin_dir / "npx"
            npx.write_text(FAKE_NPX, newline="\n", encoding="utf-8")
            npx.chmod(npx.stat().st_mode | stat.S_IXUSR)
        return bin_dir

    def run_hook(self, file, bin_dir=None, project=None, cwd=None, **env):
        cwd = cwd or self.project
        payload = {"tool_input": {"file_path": str(file)}}
        environ = {
            "PATH": str(bin_dir or self.bin),
            "STUB_LOG": str(self.log),
            "CLAUDE_PROJECT_DIR": str(self.project if project is None else project),
            # A shell keeps PWD as the path it was given, so a symlinked TMPDIR stays one.
            "PWD": str(cwd),
            **env,
        }
        # A value of None leaves the variable unset.
        environ = {k: v for k, v in environ.items() if v is not None}
        return subprocess.run(
            [BASH, str(SCRIPT)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            cwd=cwd,
            env=environ,
            timeout=30,
            check=False,
        )

    def npx_calls(self):
        return self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []

    def npx_pwd(self):
        return pathlib.Path(self.log.with_name("npx.log.pwd").read_text(encoding="utf-8").strip())

    def no_npx(self):
        return self.make_bin(self.tmp / "no-npx-bin", with_jq=True, with_npx=False)

    def no_jq(self):
        return self.make_bin(self.tmp / "no-jq-bin", with_jq=False)

    def test_a_non_script_file_exits_0_and_never_calls_npx(self):
        for name in ("README.md", "data.json", "style.css", "mod.py", "mod.ts.bak", "Makefile"):
            with self.subTest(name=name):
                result = self.run_hook(name, STUB_FINDINGS="1")
                self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.npx_calls(), [])

    def test_every_script_extension_is_linted(self):
        names = ["a.ts", "a.tsx", "a.js", "a.jsx", "a.mts", "a.cts", "a.mjs", "a.cjs"]
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(self.run_hook(name).returncode, 0)
        self.assertEqual(len(self.npx_calls()), len(names))

    def test_a_clean_file_exits_0(self):
        result = self.run_hook("mod.ts")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        self.assertEqual(len(self.npx_calls()), 1)

    def test_findings_exit_2_with_them_on_stderr(self):
        result = self.run_hook("mod.tsx", STUB_FINDINGS="1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("mod.tsx", result.stderr)
        self.assertIn("no-unused-vars", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_only_the_projects_eslint_runs_with_no_fix_and_no_ignore_warning(self):
        self.run_hook(self.project / "mod.ts", STUB_FINDINGS="1")
        self.assertEqual(
            self.npx_calls(),
            [f"--no-install eslint --max-warnings 0 --no-warn-ignored {self.project.resolve()}/mod.ts"],
        )

    def test_a_missing_jq_exits_1_and_says_so_on_stderr(self):
        result = self.run_hook("mod.ts", bin_dir=self.no_jq(), STUB_FINDINGS="1")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stderr,
            "ad-typescript lint hook: jq is not on PATH, so ESLint did not check the edited file.\n",
        )
        self.assertEqual(self.npx_calls(), [])

    def test_a_missing_jq_reads_an_escaped_quote_in_the_path(self):
        result = self.run_hook('a"b.ts', bin_dir=self.no_jq())
        self.assertEqual(result.returncode, 1)
        self.assertIn("jq is not on PATH", result.stderr)

    def test_a_missing_jq_and_no_package_json_exits_0_silently(self):
        bare = self.tmp / "bare"
        bare.mkdir()
        result = self.run_hook("mod.ts", bin_dir=self.no_jq(), project=bare, STUB_FINDINGS="1")
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.npx_calls(), [])

    def test_a_missing_jq_and_a_non_script_file_exits_0_silently(self):
        result = self.run_hook("notes.md", bin_dir=self.no_jq(), STUB_FINDINGS="1")
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.npx_calls(), [])

    def test_a_project_without_package_json_exits_0_and_never_calls_npx(self):
        bare = self.tmp / "bare"
        bare.mkdir()
        result = self.run_hook("mod.ts", project=bare, cwd=bare, STUB_FINDINGS="1")
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.npx_calls(), [])

    def test_npx_runs_from_the_project_root_and_still_gets_the_edited_file(self):
        sub = self.project / "src"
        sub.mkdir()
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        for file, cwd, expected in (
            (self.project / "mod.ts", elsewhere, self.project / "mod.ts"),
            ("mod.ts", sub, sub / "mod.ts"),
        ):
            with self.subTest(file=str(file)):
                self.log.unlink(missing_ok=True)
                result = self.run_hook(file, cwd=cwd)
                self.assertEqual((result.returncode, result.stderr), (0, ""))
                self.assertEqual(self.npx_pwd().resolve(), self.project.resolve())
                arg = self.npx_calls()[0].rsplit(" ", 1)[1]
                self.assertEqual(pathlib.Path(arg).resolve(), expected.resolve())

    def test_resolving_a_relative_root_ignores_cdpath(self):
        decoy = self.tmp / "decoy"
        (decoy / "project").mkdir(parents=True)
        result = self.run_hook(
            self.project / "mod.ts", project="project", cwd=self.tmp, CDPATH=str(decoy)
        )
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(len(self.npx_calls()), 1)
        self.assertEqual(self.npx_pwd().resolve(), self.project.resolve())

    def assert_linted(self, result):
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(len(self.npx_calls()), 1)

    def test_a_symlinked_root_with_a_physical_file_path_is_linted(self):
        link = self.tmp / "link"
        link.symlink_to(self.project)
        self.assert_linted(self.run_hook(self.project / "mod.ts", project=link))

    def test_a_physical_root_with_a_file_path_under_a_symlink_is_linted(self):
        link = self.tmp / "link"
        link.symlink_to(self.project)
        self.assert_linted(self.run_hook(link / "mod.ts"))

    def test_a_root_with_a_trailing_slash_is_linted(self):
        self.assert_linted(self.run_hook(self.project / "mod.ts", project=f"{self.project}/"))

    def test_an_unset_project_dir_means_the_starting_directory(self):
        self.assert_linted(self.run_hook("mod.ts", project=None, CLAUDE_PROJECT_DIR=None))
        self.assertEqual(self.npx_pwd().resolve(), self.project.resolve())
        self.log.unlink()
        bare = self.tmp / "bare"
        bare.mkdir()
        result = self.run_hook("mod.ts", cwd=bare, CLAUDE_PROJECT_DIR=None, STUB_FINDINGS="1")
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.npx_calls(), [])

    def test_a_root_that_does_not_exist_is_not_a_project(self):
        result = self.run_hook("mod.ts", project=self.tmp / "missing", STUB_FINDINGS="1")
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.npx_calls(), [])

    def test_a_dotdot_path_that_leaves_the_root_is_skipped(self):
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        for file in (self.project / ".." / "elsewhere" / "x.ts", "../elsewhere/x.ts"):
            with self.subTest(file=str(file)):
                result = self.run_hook(file, STUB_FINDINGS="1")
                self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.npx_calls(), [])

    def test_a_file_in_a_directory_that_does_not_exist_is_skipped(self):
        result = self.run_hook(self.project / "nope" / "x.ts", STUB_FINDINGS="1")
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.npx_calls(), [])

    def test_a_missing_npx_exits_1_and_says_so_on_stderr(self):
        result = self.run_hook("mod.ts", bin_dir=self.no_npx())
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stderr,
            "ad-typescript lint hook: npx is not on PATH, so ESLint did not check the edited file.\n",
        )

    def test_a_file_outside_the_project_is_skipped(self):
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        outside = self.run_hook(elsewhere / "scratch.ts", STUB_FINDINGS="1")
        self.assertEqual((outside.returncode, outside.stderr), (0, ""))
        self.assertEqual(self.npx_calls(), [])
        relative = self.run_hook("scratch.ts", cwd=elsewhere, STUB_FINDINGS="1")
        self.assertEqual((relative.returncode, relative.stderr), (0, ""))
        self.assertEqual(self.npx_calls(), [])
        (self.project / "src").mkdir()
        inside = self.run_hook(self.project / "src" / "mod.ts", cwd=elsewhere, STUB_FINDINGS="1")
        self.assertEqual(inside.returncode, 2)
        self.assertEqual(len(self.npx_calls()), 1)


class HooksJsonTest(unittest.TestCase):
    def test_post_tool_use_runs_the_script_on_edits(self):
        entries = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]["PostToolUse"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["matcher"], "Write|Edit|MultiEdit")
        command = entries[0]["hooks"][0]["command"]
        self.assertEqual(command, 'bash "${CLAUDE_PLUGIN_ROOT}/hooks/lint-on-edit.sh"')
        self.assertTrue(SCRIPT.is_file())


if __name__ == "__main__":
    unittest.main()
