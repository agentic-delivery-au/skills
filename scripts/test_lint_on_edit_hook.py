#!/usr/bin/env python3
"""Tests for ad-python's lint-on-edit PostToolUse hook, with a fake `uv` first on PATH.

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
SCRIPT = ROOT / "plugins" / "ad-python" / "hooks" / "lint-on-edit.sh"
HOOKS_JSON = ROOT / "plugins" / "ad-python" / "hooks" / "hooks.json"

FAKE_UV = r"""#!/usr/bin/env bash
printf '%s\n' "$*" >>"$STUB_LOG"
pwd >"$STUB_LOG.pwd"
[ -z "${STUB_FINDINGS:-}" ] && exit 0
echo "${!#}:1:8: F401 [*] \`os\` imported but unused"
exit 1
"""

BASH, JQ = shutil.which("bash"), shutil.which("jq")


@unittest.skipUnless(BASH and JQ, "needs bash and jq")
class LintOnEditTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        tmp = pathlib.Path(self._tmp.name)
        self.bin = self.make_bin(tmp / "bin", with_jq=True)
        self.log = tmp / "uv.log"
        self.project = tmp / "project"
        self.project.mkdir()
        (self.project / "uv.lock").write_text("", encoding="utf-8")

    @staticmethod
    def make_bin(bin_dir, *, with_jq):
        """A PATH holding only bash, the fake uv, and jq if asked."""
        bin_dir.mkdir()
        (bin_dir / "bash").symlink_to(BASH)
        if with_jq:
            (bin_dir / "jq").symlink_to(JQ)
        uv = bin_dir / "uv"
        uv.write_text(FAKE_UV, newline="\n", encoding="utf-8")
        uv.chmod(uv.stat().st_mode | stat.S_IXUSR)
        return bin_dir

    def run_hook(self, file, bin_dir=None, project=None, cwd=None, **env):
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
                **env,
            },
            timeout=30,
            check=False,
        )

    def uv_calls(self):
        return self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []

    def test_a_non_python_file_exits_0_and_never_calls_uv(self):
        result = self.run_hook("README.md", STUB_FINDINGS="1")
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.uv_calls(), [])

    def test_a_clean_file_exits_0(self):
        result = self.run_hook("mod.py")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        self.assertEqual(len(self.uv_calls()), 1)

    def test_findings_exit_2_with_them_on_stderr(self):
        result = self.run_hook("mod.pyi", STUB_FINDINGS="1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("mod.pyi:1:8: F401", result.stderr)

    def test_ruff_honours_excludes_and_is_never_given_a_fix_flag(self):
        self.run_hook("mod.py", STUB_FINDINGS="1")
        self.assertEqual(
            self.uv_calls(),
            [f"run ruff check --force-exclude --output-format concise {pathlib.Path.cwd()}/mod.py"],
        )

    def test_a_missing_jq_exits_1_and_says_so_on_stderr(self):
        no_jq = self.make_bin(pathlib.Path(self._tmp.name) / "no-jq-bin", with_jq=False)
        result = self.run_hook("mod.py", bin_dir=no_jq, STUB_FINDINGS="1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("jq is not on PATH", result.stderr)
        self.assertEqual(self.uv_calls(), [])

    def test_uv_runs_from_the_project_root_and_still_gets_the_edited_file(self):
        elsewhere = pathlib.Path(self._tmp.name) / "elsewhere"
        elsewhere.mkdir()
        for file, expected in (
            (self.project / "mod.py", self.project / "mod.py"),
            ("mod.py", elsewhere / "mod.py"),
        ):
            with self.subTest(file=str(file)):
                self.log.unlink(missing_ok=True)
                result = self.run_hook(file, cwd=elsewhere)
                self.assertEqual((result.returncode, result.stderr), (0, ""))
                pwd = pathlib.Path(self.log.with_name("uv.log.pwd").read_text().strip())
                self.assertEqual(pwd.resolve(), self.project.resolve())
                self.assertTrue(self.uv_calls()[0].endswith(f" {expected}"))

    def test_a_missing_jq_reads_an_escaped_quote_in_the_path(self):
        no_jq = self.make_bin(pathlib.Path(self._tmp.name) / "no-jq-bin", with_jq=False)
        result = self.run_hook('a"b.py', bin_dir=no_jq)
        self.assertEqual(result.returncode, 1)
        self.assertIn("jq is not on PATH", result.stderr)

    def test_a_missing_jq_and_no_uv_lock_exits_0_silently(self):
        no_jq = self.make_bin(pathlib.Path(self._tmp.name) / "no-jq-bin", with_jq=False)
        bare = pathlib.Path(self._tmp.name) / "bare"
        bare.mkdir()
        result = self.run_hook("mod.py", bin_dir=no_jq, project=bare, STUB_FINDINGS="1")
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.uv_calls(), [])

    def test_a_missing_jq_and_a_non_python_file_exits_0_silently(self):
        no_jq = self.make_bin(pathlib.Path(self._tmp.name) / "no-jq-bin", with_jq=False)
        result = self.run_hook("notes.md", bin_dir=no_jq, STUB_FINDINGS="1")
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.uv_calls(), [])

    def test_a_project_without_uv_lock_exits_0_and_never_calls_uv(self):
        bare = pathlib.Path(self._tmp.name) / "bare"
        bare.mkdir()
        result = self.run_hook("mod.py", project=bare, STUB_FINDINGS="1")
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.uv_calls(), [])


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
