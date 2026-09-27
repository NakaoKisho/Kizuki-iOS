"""Generate, validate, and submit Kizuki issue bodies using GitHub CLI."""

import argparse
from pathlib import Path
import re
import subprocess
import sys
import tempfile


TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
REPOSITORY = "github.com/NakaoKisho/Kizuki-iOS"
KINDS = ("task", "decision")


def sections(text):
    """Split level-two sections, ignoring headings inside fenced code blocks."""
    result = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
        elif marker:
            fence = marker[1]
        else:
            heading = re.match(r"^ {0,3}##(?:[ \t]+|$)(.*)$", line)
            if heading:
                name = re.sub(r"[ \t]+#+[ \t]*$", "", heading[1]).strip()
                result.append((name, []))
                continue
            if re.fullmatch(r" {0,3}-+[ \t]*", line):
                raise ValueError("下線形式の見出し・ハイフンだけの区切り線は使わず、テンプレートの見出しを使ってください。")
            if not result and line.strip():
                raise ValueError("最初の必須見出しより前には本文を置かないでください。")
        if result:
            result[-1][1].append(line)
    if fence:
        raise ValueError("コードフェンスが閉じられていません。")
    return result


def template(kind):
    return (TEMPLATES / f"{kind}.md").read_text(encoding="utf-8")


def validate(kind, body):
    expected = [heading for heading, _ in sections(template(kind))]
    actual = sections(body)
    if [heading for heading, _ in actual] != expected:
        raise ValueError("必須見出しと順序をテンプレートに合わせてください: " + " / ".join(expected))
    if re.search(r"<!--\s*TODO\b", body, re.IGNORECASE):
        raise ValueError("テンプレートのTODOコメントを記入済みの内容に置き換えてください。")
    for heading, lines in actual:
        content = re.sub(r"<!--.*?-->", "", "\n".join(lines), flags=re.DOTALL)
        # Empty bullets, checkboxes, and heading markers are not filled content.
        visible = re.sub(r"[\s#*\-+\[\]`~>]", "", content)
        if not visible:
            raise ValueError(f"「{heading}」に内容を記入してください。")


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest="command", required=True)
    for name in ("init", "validate", "create"):
        command = commands.add_parser(name)
        command.add_argument("--type", choices=KINDS, required=True, dest="kind")
        if name == "init":
            command.add_argument("--output", type=Path, required=True)
        else:
            command.add_argument("--body-file", type=Path, required=True)
        if name == "create":
            command.add_argument("--title", required=True)
    return cli


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "init":
            content = template(args.kind)
            with args.output.open("x", encoding="utf-8", newline="\n") as output:
                output.write(content)
            print(f"テンプレートを作成しました: {args.output}")
            return 0

        body = args.body_file.read_text(encoding="utf-8-sig")
        validate(args.kind, body)
        if args.command == "validate":
            print("必須項目の検証に成功しました。")
            return 0
        if not args.title.strip():
            raise ValueError("タイトルを空にはできません。")

        # Send exactly the validated text, even if the source file changes later.
        with tempfile.TemporaryDirectory(prefix="kizuki-issue-") as directory:
            snapshot = Path(directory) / "body.md"
            snapshot.write_text(body, encoding="utf-8")
            command = ["gh", "issue", "create", "--repo", REPOSITORY,
                       "--title", args.title, "--body-file", str(snapshot)]
            if args.kind == "decision":
                command.extend(["--label", "decision"])
            result = subprocess.run(command, shell=False, check=False)
        if result.returncode:
            print("ghが非0で終了しました。作成状況を確認してから再実行してください。", file=sys.stderr)
            return result.returncode if result.returncode > 0 else 1
        return 0
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Issue操作に失敗しました: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
