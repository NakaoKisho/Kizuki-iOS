import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys


SCRIPT = Path(__file__).resolve().parents[1] / "output_gate.py"
spec = importlib.util.spec_from_file_location("output_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class OutputGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "src").mkdir()
        (self.root / "src/a.txt").write_text("first", encoding="utf-8")
        self.run = gate.prepare(self.root, "issue-1", "design", ["reviewer"], ["src"])

    def report(self, run=None, **changes):
        run = run or self.run
        value = dict(run_id=run.name, agent="reviewer", fingerprint=gate.fingerprint(self.root, run),
                     status="ready", summary="確認した。", evidence=["src/a.txt"], findings=[])
        value.update(changes)
        path = run / "reviewer.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def payload(self, path, **changes):
        value = dict(agent_type="reviewer", last_assistant_message="REPORT_PATH=" + path.relative_to(self.root).as_posix())
        value.update(changes)
        return value

    def test_valid_report_passes_hook_and_parent(self):
        path = self.report()
        self.assertEqual(gate.hook(self.root, self.payload(path)), {})
        gate.check(self.root, self.run)

    def test_missing_and_previous_run_are_not_accepted(self):
        self.report()
        new = gate.prepare(self.root, "issue-1", "design", ["reviewer"], ["src"])
        self.assertNotEqual(new, self.run)
        with self.assertRaises(ValueError): gate.check(self.root, new)
        path = self.report(new, run_id=self.run.name)
        self.assertEqual(gate.hook(self.root, self.payload(path))["decision"], "block")

    def test_changes_additions_and_deletions_invalidate_reports(self):
        for mutation in ("edit", "add", "delete"):
            with self.subTest(mutation=mutation):
                target = self.root / "src/a.txt"
                target.write_text("first", encoding="utf-8")
                self.report()
                if mutation == "edit": target.write_text("second", encoding="utf-8")
                elif mutation == "add": (self.root / "src/new.txt").write_text("new", encoding="utf-8")
                else: target.unlink()
                with self.assertRaises(ValueError): gate.check(self.root, self.run)
                (self.root / "src/new.txt").unlink(missing_ok=True)

    def test_non_ready_reports_are_valid_but_cannot_advance(self):
        for status in ("needs_changes", "blocked"):
            path = self.report(status=status)
            self.assertEqual(gate.hook(self.root, self.payload(path)), {})
            with self.assertRaises(ValueError): gate.check(self.root, self.run)

    def test_findings_block_parent(self):
        for severity in ("重大", "通常"):
            path = self.report(findings=[dict(id="F1", severity=severity, message="修正が必要")])
            self.assertEqual(gate.hook(self.root, self.payload(path)), {})
            with self.assertRaises(ValueError): gate.check(self.root, self.run)

    def test_ready_requires_evidence(self):
        path = self.report(evidence=[])
        self.assertEqual(gate.hook(self.root, self.payload(path))["decision"], "block")
        with self.assertRaises(ValueError): gate.check(self.root, self.run)

    def test_malformed_and_wrong_agent_reports_block(self):
        for changes in (dict(agent="other"), dict(status="pass"), dict(summary=""), dict(evidence="text"),
                        dict(findings=[dict(id="F1", severity="unknown", message="bad")]), dict(fingerprint=3)):
            path = self.report(**changes)
            self.assertEqual(gate.hook(self.root, self.payload(path))["decision"], "block")
        path = self.report()
        self.assertEqual(gate.hook(self.root, self.payload(path, agent_type="other"))["decision"], "block")

    def test_invalid_hook_inputs_stop_without_pass_or_sensitive_diagnostics(self):
        for payload in ({}, [], {"last_assistant_message": "REPORT_PATH=../../secret"},
                        {"last_assistant_message": "REPORT_PATH=secret-TOKEN", "stop_hook_active": True}):
            result = gate.hook(self.root, payload)
            self.assertNotIn("secret-TOKEN", json.dumps(result))
            if isinstance(payload, dict) and payload.get("stop_hook_active"):
                self.assertIs(result["continue"], False)
            else: self.assertEqual(result["decision"], "block")

    def test_symlinks_and_path_escape_rejected(self):
        path = self.report()
        saved = path.read_text()
        path.unlink()
        outside = self.root / "outside.json"
        outside.write_text(saved)
        path.symlink_to(outside)
        with self.assertRaises(ValueError): gate.check(self.root, self.run)
        for target in ("../outside", "/tmp", ".agent-output", "src/../src"):
            with self.assertRaises(ValueError): gate.prepare(self.root, "task", "phase", ["reviewer"], [target])
        (self.root / "src/link").symlink_to(outside)
        with self.assertRaises(ValueError): gate.fingerprint(self.root, self.run)

    def test_manifest_and_required_agents_are_validated(self):
        second = gate.prepare(self.root, "task", "phase", ["reviewer", "other"], ["src"])
        self.report(second)
        with self.assertRaises(ValueError): gate.check(self.root, second)
        manifest = self.run / "request.json"
        value = json.loads(manifest.read_text())
        value["agents"] = "reviewer"
        manifest.write_text(json.dumps(value))
        with self.assertRaises(ValueError): gate.check(self.root, self.run)

    def test_cli_and_configured_posix_hook_from_nested_directory(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        copied = self.root / ".agents/skills/kizuki-agent-handoff/scripts/output_gate.py"
        copied.parent.mkdir(parents=True)
        copied.write_bytes(SCRIPT.read_bytes())
        command = [sys.executable, "-B", str(copied)]
        def cli(*args, payload=None):
            return subprocess.run(command + list(args), cwd=self.root / "src", input=payload,
                                  text=True, capture_output=True)
        prepared = cli("prepare", "--task", "task", "--phase", "test", "--agent", "reviewer", "--target", "src")
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        run = prepared.stdout.strip()
        self.assertNotEqual(cli("check", "--run", run).returncode, 0)
        self.assertEqual(cli("fingerprint", "--run", run).returncode, 0)
        path = self.report(self.root / run)
        self.assertEqual(cli("check", "--run", run).returncode, 0)
        payload = json.dumps(self.payload(path))
        hooks_path = SCRIPT.parents[4] / ".codex/hooks.json"
        config = json.loads(hooks_path.read_text())
        hook = config["hooks"]["SubagentStop"][0]["hooks"][0]
        self.assertIn("commandWindows", hook)
        self.assertNotIn("$", hook["commandWindows"])
        result = subprocess.run(["sh", "-c", hook["command"]], cwd=self.root / "src",
                                input=payload, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {})
        # Exercise the Windows launcher Python body/argv without claiming Windows shell coverage.
        launcher = hook["commandWindows"].split('"')[1]
        self.assertTrue(hook["commandWindows"].endswith('" hook'))
        result = subprocess.run([sys.executable, "-B", "-c", launcher, "hook"], cwd=self.root / "src",
                                input=payload, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {})
        invalid = cli("hook", payload="not-json SECRET")
        self.assertEqual(invalid.returncode, 0)
        self.assertEqual(json.loads(invalid.stdout)["decision"], "block")
        self.assertNotIn("SECRET", invalid.stdout + invalid.stderr)


if __name__ == "__main__":
    unittest.main()
