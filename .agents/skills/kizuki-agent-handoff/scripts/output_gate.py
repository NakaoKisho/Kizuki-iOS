"""Subagent reports: isolated runs, current target fingerprints, and completion gates."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import uuid


class Invalid(ValueError):
    pass


def require(condition):
    if not condition:
        raise Invalid("成果物契約を満たしていません。依頼と報告を確認してください。")


def text(value):
    return isinstance(value, str) and bool(value.strip())


def name(value):
    return isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9-]*", value) is not None


def safe_path(root, value):
    require(isinstance(value, str) and value and "\\" not in value and ":" not in value)
    parts = value.split("/")
    require(all(part not in ("", ".", "..") for part in parts))
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink())
    require(path.resolve().is_relative_to(root.resolve()))
    return path


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value)
        value[key] = item
    return value


def read_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)
    except (OSError, UnicodeError, ValueError):
        raise Invalid("報告または依頼を読み取れません。") from None
    require(isinstance(value, dict))
    return value


def run_path(root, run):
    if isinstance(run, Path) and run.is_absolute():
        try:
            run = run.relative_to(root).as_posix()
        except ValueError:
            raise Invalid("作業ディレクトリ外は指定できません。") from None
    require(isinstance(run, str))
    parts = run.split("/")
    require(len(parts) == 2 and parts[0] == ".agent-output")
    try:
        require(str(uuid.UUID(parts[1])) == parts[1])
    except (ValueError, AttributeError):
        raise Invalid("実行IDが不正です。") from None
    return safe_path(root, run)


def manifest(root, run):
    path = run_path(root, run)
    value = read_json(safe_path(root, (path.relative_to(root) / "request.json").as_posix()))
    require(set(value) == {"run_id", "task", "phase", "agents", "targets"})
    require(value["run_id"] == path.name and text(value["task"]) and text(value["phase"]))
    require(isinstance(value["agents"], list) and value["agents"] and all(name(x) for x in value["agents"]))
    require(len(set(value["agents"])) == len(value["agents"]) and "request" not in value["agents"])
    require(isinstance(value["targets"], list) and value["targets"] and all(text(x) for x in value["targets"]))
    require(len(set(value["targets"])) == len(value["targets"]))
    return path, value


def target_digest(root, request):
    entries = []
    for target in sorted(request["targets"]):
        require(target.split("/")[0] not in (".agent-output", ".git"))
        path = safe_path(root, target)
        require(path.exists() and (path.is_dir() or path.is_file()))
        candidates = [path]
        if path.is_dir():
            candidates.extend(sorted(path.rglob("*")))
        for item in candidates:
            relative = item.relative_to(root).as_posix()
            safe_path(root, relative)
            require(item.is_dir() or item.is_file())
            entries.append([relative, "directory" if item.is_dir() else hashlib.sha256(item.read_bytes()).hexdigest()])
    # Bind both the current files and the request; changes to task/participants invalidate reports.
    encoded = json.dumps([request, entries], sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def prepare(root, task, phase, agents, targets):
    require(text(task) and text(phase))
    require(isinstance(agents, list) and agents and all(name(x) for x in agents))
    require(len(set(agents)) == len(agents) and "request" not in agents)
    require(isinstance(targets, list) and targets and all(text(x) for x in targets))
    require(len(set(targets)) == len(targets))
    request = dict(run_id=str(uuid.uuid4()), task=task, phase=phase, agents=agents, targets=targets)
    target_digest(root, request)
    base = safe_path(root, ".agent-output")
    base.mkdir(exist_ok=True)
    run = base / request["run_id"]
    run.mkdir()  # Never reuse or overwrite an existing run.
    with (run / "request.json").open("x", encoding="utf-8") as output:
        json.dump(request, output, ensure_ascii=False, indent=2)
        output.write("\n")
    return run


def fingerprint(root, run):
    _, request = manifest(root, run)
    return target_digest(root, request)


def report(root, run, agent, expected_fingerprint):
    path, request = manifest(root, run)
    require(agent in request["agents"])
    value = read_json(safe_path(root, (path.relative_to(root) / f"{agent}.json").as_posix()))
    require(set(value) == {"run_id", "agent", "fingerprint", "status", "summary", "evidence", "findings"})
    require(value["run_id"] == path.name and value["agent"] == agent)
    require(value["fingerprint"] == expected_fingerprint)
    require(value["status"] in ("ready", "needs_changes", "blocked") and text(value["summary"]))
    require(isinstance(value["evidence"], list) and all(text(x) for x in value["evidence"]))
    require(value["status"] != "ready" or bool(value["evidence"]))
    require(isinstance(value["findings"], list))
    ids = []
    for finding in value["findings"]:
        require(isinstance(finding, dict) and set(finding) == {"id", "severity", "message"})
        require(text(finding["id"]) and text(finding["message"]))
        require(finding["severity"] in ("重大", "通常", "提案"))
        ids.append(finding["id"])
    require(len(set(ids)) == len(ids))
    return value


def check(root, run):
    path, request = manifest(root, run)
    digest = target_digest(root, request)
    for agent in request["agents"]:
        value = report(root, path, agent, digest)
        require(value["status"] == "ready")
        require(not any(x["severity"] in ("重大", "通常") for x in value["findings"]))


def rejection(payload):
    reason = "報告の検証に失敗しました。指定された実行ID・出力先・対象版・JSON契約を確認してください。"
    if isinstance(payload, dict) and payload.get("stop_hook_active") is True:
        return {"continue": False, "stopReason": reason + "親のcheckが通るまで次工程へ進めません。"}
    return {"decision": "block", "reason": reason}


def hook(root, payload):
    try:
        require(isinstance(payload, dict))
        require(name(payload.get("agent_type")))
        message = payload.get("last_assistant_message")
        require(isinstance(message, str))
        markers = re.findall(r"^REPORT_PATH=([^\r\n]+)$", message, re.MULTILINE)
        require(len(markers) == 1)
        relative = markers[0]
        safe_path(root, relative)
        parts = PurePosixPath(relative).parts
        require(len(parts) == 3 and parts[2] == payload["agent_type"] + ".json")
        run = run_path(root, "/".join(parts[:2]))
        report(root, run, payload["agent_type"], fingerprint(root, run))
        return {}
    except (OSError, ValueError, TypeError):
        return rejection(payload)


def root_directory():
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], check=True, capture_output=True, text=True)
    return Path(result.stdout.strip()).resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("prepare")
    init.add_argument("--task", required=True)
    init.add_argument("--phase", required=True)
    init.add_argument("--agent", action="append", required=True)
    init.add_argument("--target", action="append", required=True)
    for verb in ("fingerprint", "check"):
        commands.add_parser(verb).add_argument("--run", required=True)
    commands.add_parser("hook")
    args = parser.parse_args()
    payload = None
    if args.command == "hook":
        try:
            payload = json.load(sys.stdin, object_pairs_hook=unique_object)
        except (ValueError, UnicodeError):
            pass
    try:
        root = root_directory()
        if args.command == "hook":
            print(json.dumps(hook(root, payload), ensure_ascii=False))
        elif args.command == "prepare":
            print(prepare(root, args.task, args.phase, args.agent, args.target).relative_to(root).as_posix())
        elif args.command == "fingerprint":
            print(fingerprint(root, args.run))
        else:
            check(root, args.run)
            print("pass")
        return 0
    except (OSError, ValueError, subprocess.SubprocessError):
        if args.command == "hook":
            print(json.dumps(rejection(payload), ensure_ascii=False))
            return 0
        print("検証に失敗しました。依頼・対象ファイル・報告を確認してください。", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
