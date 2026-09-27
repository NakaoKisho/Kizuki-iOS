# エージェント出力の契約

## 親の準備

リポジトリ内でprepareを実行し、表示されたrunパスを委譲先へ渡す。対象には、確認すべきファイルかディレクトリを明示する。新しいファイルを作る工程では、その親ディレクトリを対象にする。出力先そのものやGit内部は対象に含めない。

```bash
python3 .agents/skills/kizuki-agent-handoff/scripts/output_gate.py prepare --task record-entry --phase design --agent ios-tech-lead --agent user-advocate --target .codex/rules/product
```

prepareは実行ごとのIDと依頼を作り、既存runを再利用しない。対象を広げる場合や別の実行・再レビューでは新しいrunを用意する。

## 担当の報告

[報告テンプレート](report.json)を使い、指定runの`<agent>.json`に報告する。フィールドは次のとおり。

- `run_id`：prepareが発行した実行ID
- `agent`：指定された専門エージェント名
- `fingerprint`：報告対象の現在の内容を表すハッシュ
- `status`：`ready`（次工程へ渡せる）、`needs_changes`（修正が必要）、`blocked`（検証や作業を完了できない）
- `summary`：結論
- `evidence`：根拠・対象箇所・検証コマンドと結果・追加成果物への参照。readyでは空にしない
- `findings`：今回残っている指摘。各要素は`id`・`severity`（重大／通常／提案）・`message`。指摘がなければ空配列

fingerprintは、実際に確認した対象の版について次のコマンドで取得する。`RUN_ID`をprepareの出力に合わせて置き換える。

```bash
python3 .agents/skills/kizuki-agent-handoff/scripts/output_gate.py fingerprint --run .agent-output/RUN_ID
```

指摘IDは再レビューで維持し、前回指摘の解消・未解消・対象外と根拠はevidenceへ記録する。重大・通常が未解消ならreadyにしない。テスト結果にはpass・failed・verification gapを区別して記載する。未実施を成功と書かない。

最終メッセージには次の形式の行を1つだけ含める。パスは作業rootからの相対パスにする。

```text
REPORT_PATH=.agent-output/RUN_ID/ios-tech-lead.json
```

生の体調データや秘密情報を含めない。コード・Figma・図など成果物の内容は工程に合わせて自由に作り、報告から参照する。

## 親の検査

```bash
python3 .agents/skills/kizuki-agent-handoff/scripts/output_gate.py check --run .agent-output/RUN_ID
```

全担当の出力、実行ID、現在の対象ハッシュ、ready、未解消の重大・通常がないことを確認する。ハッシュは対象配下の追加・削除・内容変更も検出する。古い報告、欠損、不正、needs_changes、blockedは非0になる。

SubagentStop hookは報告ファイルが契約を満たすかを確認する。needs_changesやblockedを正直に報告すること自体は許可するが、親checkは通さない。形式の通過と内容の受入を区別する。

```bash
python3 -B -m unittest discover -s .agents/skills/kizuki-agent-handoff/scripts/tests -v
```

定義の検査を含むテストにはPython 3.11以上を使用する。Windowsでは環境に応じてpython3をpy -3等に置き換える。報告はGitへ追加せず、必要な結果だけをIssue・PRへ要約する。
