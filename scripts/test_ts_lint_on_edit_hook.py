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


@unittest.skipUnless(BASH and JQ, "needs bash and jq")
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
    def make_bin(bin_dir, *, with_jq):
        """A PATH holding only bash, the fake npx, and jq if asked."""
        bin_dir.mkdir()
        (bin_dir / "bash").symlink_to(BASH)
        if with_jq:
            (bin_dir / "jq").symlink_to(JQ)
        npx = bin_dir / "npx"
        npx.write_text(FAKE_NPX, newline="\n", encoding="utf-8")
        npx.chmod(npx.stat().st_mode | stat.S_IXUSR)
        return bin_dir

    def run_hook(self, file, bin_dir=None, project=None, cwd=None, **env):
        cwd = cwd or self.project
        payload = {"tool_input": {"file_path": str(file)}}
        return subprocess.run(
            [BASH, str(SCRIPT)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            cwd=cwd,
            env={
                "PATH": str(bin_dir or self.bin),
                "STUB_LOG": str(self.log),
                "CLAUDE_PROJECT_DIR": str(project or self.project),
                # A shell keeps PWD as the path it was given, so a symlinked TMPDIR stays one.
                "PWD": str(cwd),
                **env,
            },
            timeout=30,
            check=False,
        )

    def npx_calls(self):
        return self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []

    def npx_pwd(self):
        return pathlib.Path(self.log.with_name("npx.log.pwd").read_text(encoding="utf-8").strip())

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
            [f"--no-install eslint --max-warnings 0 --no-warn-ignored {self.project}/mod.ts"],
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

    def test_cd_to_the_root_ignores_cdpath(self):
        sub = self.project / "src"
        sub.mkdir()
        decoy = self.tmp / "decoy"
        (decoy / "project").mkdir(parents=True)
        result = self.run_hook(self.project / "mod.ts", cwd=sub, CDPATH=str(decoy))
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.npx_pwd().resolve(), self.project.resolve())

    def test_a_file_outside_the_project_is_skipped(self):
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        outside = self.run_hook(elsewhere / "scratch.ts", STUB_FINDINGS="1")
        self.assertEqual((outside.returncode, outside.stderr), (0, ""))
        self.assertEqual(self.npx_calls(), [])
        relative = self.run_hook("scratch.ts", cwd=elsewhere, STUB_FINDINGS="1")
        self.assertEqual((relative.returncode, relative.stderr), (0, ""))
        self.assertEqual(self.npx_calls(), [])
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
