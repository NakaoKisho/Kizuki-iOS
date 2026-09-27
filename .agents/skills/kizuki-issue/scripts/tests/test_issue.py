"""Issue CLI boundary tests; no network access or real GitHub writes."""

import contextlib
import importlib.util
import io
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "issue.py"
spec = importlib.util.spec_from_file_location("issue", SCRIPT)
issue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(issue)


class IssueTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.body_file = Path(self.directory.name) / "本文 draft.md"

    def filled(self, kind="decision"):
        return re.sub(r"<!-- TODO:.*?-->", "記入済みの内容。", issue.template(kind))

    def invoke(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return issue.main(list(args))

    def create(self, kind="decision", title="判断: 記録の仕様"):
        return self.invoke("create", "--type", kind, "--title", title,
                           "--body-file", str(self.body_file))

    def test_init_is_offline_and_never_overwrites(self):
        for kind in issue.KINDS:
            with self.subTest(kind=kind), patch.object(issue.subprocess, "run") as run:
                output = Path(self.directory.name) / f"{kind}.md"
                args = ("init", "--type", kind, "--output", str(output))
                self.assertEqual(self.invoke(*args), 0)
                self.assertEqual(output.read_text(encoding="utf-8"), issue.template(kind))
                output.write_text("existing draft", encoding="utf-8")
                self.assertNotEqual(self.invoke(*args), 0)
                self.assertEqual(output.read_text(encoding="utf-8"), "existing draft")
                run.assert_not_called()

    def test_unfilled_missing_reordered_duplicate_and_empty_sections_do_not_send(self):
        good = self.filled()
        cases = [
            issue.template("decision"),
            good.replace("## 選択肢と制約", "## 未知の節"),
            good.replace("## 背景と問題", "## 決定と理由"),
            good.replace("## 背景と問題", "## 交換", 1).replace("## 選択肢と制約", "## 背景と問題", 1).replace("## 交換", "## 選択肢と制約", 1),
            good.replace("記入済みの内容。", "", 1),
            good.replace("記入済みの内容。", "<!-- empty -->\n- [ ]", 1),
            good + "\n## 追加\n記入\n",
            "preamble\n" + good,
            good + "\n```python\n",
        ]
        for body in cases:
            with self.subTest(body=body), patch.object(issue.subprocess, "run") as run:
                self.body_file.write_text(body, encoding="utf-8")
                self.assertNotEqual(self.create(), 0)
                run.assert_not_called()

    def test_code_fences_do_not_add_sections(self):
        body = self.filled() + "\n```markdown\n## not a section\n```\n"
        issue.validate("decision", body)
        issue.validate("decision", self.filled() + "\n~~~text\n## another example\n~~~\n")

    def test_alternate_markdown_h2_does_not_send(self):
        extra_headings = (" ## 追加", "  ## 追加", "   ## 追加", "##\t追加", "##", "追加\n---")
        for heading in extra_headings:
            with self.subTest(heading=heading), patch.object(issue.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run:
                self.body_file.write_text(self.filled() + "\n" + heading + "\n追加の内容\n", encoding="utf-8")
                self.assertNotEqual(self.create(), 0)
                run.assert_not_called()

    def test_wrong_template_type_does_not_send(self):
        self.body_file.write_text(self.filled("task"), encoding="utf-8")
        with patch.object(issue.subprocess, "run") as run:
            self.assertNotEqual(self.create("decision"), 0)
            run.assert_not_called()

    def test_validate_accepts_windows_utf8_bom_crlf_and_is_offline(self):
        self.body_file.write_bytes(b"\xef\xbb\xbf" + self.filled().replace("\n", "\r\n").encode())
        with patch.object(issue.subprocess, "run") as run:
            self.assertEqual(self.invoke("validate", "--type", "decision", "--body-file", str(self.body_file)), 0)
            run.assert_not_called()

    def test_create_uses_fixed_repository_labels_literal_arguments_and_snapshot(self):
        for kind in issue.KINDS:
            with self.subTest(kind=kind):
                body = self.filled(kind) + "\n文字列: $(echo test) `example`\n"
                self.body_file.write_text(body, encoding="utf-8")
                title = "仕様 $(echo test) `example` --repo other/repo"
                sent = []

                def fake_gh(command, **kwargs):
                    self.assertEqual(command[:5], ["gh", "issue", "create", "--repo", "github.com/NakaoKisho/Kizuki-iOS"])
                    self.assertEqual(command[command.index("--title") + 1], title)
                    snapshot = Path(command[command.index("--body-file") + 1])
                    self.assertNotEqual(snapshot, self.body_file)
                    self.body_file.write_text("changed after validation", encoding="utf-8")
                    self.assertEqual(snapshot.read_text(encoding="utf-8"), body)
                    self.assertEqual(kwargs, {"shell": False, "check": False})
                    self.assertEqual(command[9:], ["--label", "decision"] if kind == "decision" else [])
                    sent.append(snapshot)
                    return subprocess.CompletedProcess(command, 0)

                with patch.object(issue.subprocess, "run", side_effect=fake_gh) as run:
                    self.assertEqual(self.create(kind, title), 0)
                    run.assert_called_once()
                self.assertFalse(sent[0].exists())

    def test_empty_title_does_not_send(self):
        self.body_file.write_text(self.filled(), encoding="utf-8")
        with patch.object(issue.subprocess, "run") as run:
            self.assertNotEqual(self.create(title="  "), 0)
            run.assert_not_called()

    def test_gh_failures_propagate_without_retry(self):
        self.body_file.write_text(self.filled(), encoding="utf-8")
        for code in (1, 4, -15):
            with self.subTest(code=code), patch.object(issue.subprocess, "run", return_value=subprocess.CompletedProcess([], code)) as run:
                self.assertNotEqual(self.create(), 0)
                run.assert_called_once()
        with patch.object(issue.subprocess, "run", side_effect=FileNotFoundError("gh not installed")) as run:
            self.assertNotEqual(self.create(), 0)
            run.assert_called_once()

    def test_missing_or_invalid_utf8_body_does_not_send(self):
        with patch.object(issue.subprocess, "run") as run:
            self.assertNotEqual(self.create(), 0)
            self.body_file.write_bytes(b"\xff\xfe")
            self.assertNotEqual(self.create(), 0)
            run.assert_not_called()

    def test_cli_entrypoint_from_another_directory(self):
        args = [sys.executable, "-B", str(SCRIPT)]
        def execute(*options):
            return subprocess.run(args + list(options), cwd=self.directory.name, capture_output=True)
        self.assertEqual(execute("init", "--type", "task", "--output", str(self.body_file)).returncode, 0)
        self.assertNotEqual(execute("validate", "--type", "task", "--body-file", str(self.body_file)).returncode, 0)
        self.body_file.write_text(self.filled("task"), encoding="utf-8")
        self.assertEqual(execute("validate", "--type", "task", "--body-file", str(self.body_file)).returncode, 0)
        self.assertNotEqual(execute("validate", "--type", "unknown", "--body-file", str(self.body_file)).returncode, 0)


if __name__ == "__main__":
    unittest.main()
