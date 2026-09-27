# GitHub・ブランチ・worktree運用

要求・判断の書き方は[文書運用](../documentation/AGENTS.md)を参照する。

## ブランチと反映先

リモートにまだブランチがない初回セットアップでは、PRの比較元としてファイルを含まない共通の初期コミットから`develop`・`stg`・`main`を作成できる。実質的な変更は作業ブランチからのPRに含め、初期化の手順と例外をIssueに記録する。既存の保護を無効化・迂回しない。

通常運用の開始前に、下記の直接push防止とGitHub rulesetの利用可否・設定を確認する。保護の設定、または利用不可の場合の根拠と代替運用の合意が済むまでは初期化未完了とし、PRはDraftで作成して通常運用・マージを保留する。`origin/develop`が存在しない間は以下のworktree手順が利用可能だと扱わない。

| ブランチ | 役割 | 通常のPRの向き |
| --- | --- | --- |
| `feat/*`、`fix/*`、`docs/*`、`chore/*` | 作業単位。最新の`origin/develop`から作成 | 作業ブランチ → `develop` |
| `develop` | 開発中の変更を統合する。`dev`はこの略称 | `develop` → `stg` |
| `stg` | リリース候補の検証 | `stg` → `main` |
| `main` | 検証済みのリリース基準 | 通常の変更を直接入れない |

通常は長期ブランチへ直接pushせず、PRを使う。昇格は変更履歴をつなぐためmerge commitで行い、squash・rebaseで長期ブランチの共通履歴を切らない。作業PRはsquash mergeを基本とする。

## 直接pushの防止

初回ブランチ作成後、最初の通常作業前に次を実行する。共通Gitディレクトリにpre-pushを設置するため、worktreeを削除しても保護は残る。

```bash
python3 .codex/rules/github/scripts/install_hooks.py
```

Windowsでは環境に応じてpy -3等を使用する。既存hook・core.hooksPathと競合する場合は上書きせず、内容を確認して統合方針を決める。同じ内容の再実行は可能である。

hookは送信先のdev・develop・stg・mainへの更新・削除を拒否する。別名refspecやforceを付けても拒否する。`--no-verify`や設定変更による迂回は禁止する。ローカルhookは無効化できるため、サーバー側の保護と同等ではない。

GitHubのrulesetを利用できる環境では、この4ブランチにPR必須・削除禁止・force禁止を設定する。bypassを設けず、昇格時のmerge commitを妨げるlinear historyは必須にしない。利用できない環境で保護が有効だと報告しない。

```bash
python3 -B -m unittest discover -s .codex/rules/github/tests -v
```

## 作業開始

1. 関連Issue、受け入れ条件、作業範囲を確認する。
2. `git status --short`と`git worktree list`で、未コミット変更と既存の作業場所を確認する。他の作業の変更を持ち込まない。
3. `git fetch origin`でリモート情報を更新する。
4. 書き込み可能で未使用のパスにworktreeを作成する。次は親リポジトリのディレクトリから実行する例で、Issue番号・名前・パスは今回の作業に合わせる。

```bash
git worktree add -b docs/1-project-rules ../Kizuki-iOS-issue-1 origin/develop
cd ../Kizuki-iOS-issue-1
git status --short
```

同じブランチを複数worktreeで使わない。同じ作業ブランチで協働するサブエージェントには担当ファイルを明示し、編集を重複させない。別作業を並行するときは別ブランチ・別worktreeにする。

## コミットとPR

- 差分を確認して今回のファイルだけをstageする。秘密情報、実在の体調データ、ローカル設定、ビルド生成物を含めない。
- [レビュー調整スキル](../../../.agents/skills/kizuki-review/SKILL.md)に従って検証とレビューを行う。実行できなかった検証は成功として扱わない。
- push前に`git diff --cached --check`、コミット後に`git status --short`とbaseとの差分を確認する。
- 通常のPRのbaseは明示的に`develop`を指定する。タイトルと本文は日本語を基本とし、問題・結果・関連Issue・検証結果・残る制約を記載する。
- PR作成の依頼は、そのPRのコミット・push・作成までを含む。マージ、昇格、配布はユーザーから指示された範囲で実行する。

```bash
git push -u origin docs/1-project-rules
gh pr create --base develop --head docs/1-project-rules --title 'docs: 開発ルールを整備' --body-file /tmp/kizuki-pr-body.md
```

上記の本文ファイルは作成済みであることを前提とする。パスはOS・実行環境に合わせる。Issueは`Refs #番号`で関連付ける。既定ブランチ以外へのマージで自動closeされる前提を置かず、受け入れ条件を確認して完了を記録する。

## 昇格・修正

1. 作業PRをdevelopへ統合し、統合後の検証を行う。
2. `develop → stg`のPRを作り、対象コミット・含まれる変更・検証結果を記録する。
3. stgでリリース候補を確認し、`stg → main`のPRで反映する。検証したheadが変われば影響範囲を再検証する。

stg・mainで見つかった問題も原則developからの修正PRで直し、順に昇格する。緊急修正で例外が必要な場合は、分岐元・戻し先・検証・承認をIssueで決め、長期ブランチ間に修正漏れを残さない。

ブランチ名だけで配布環境や自動公開を保証しない。配布・署名・環境切り替えは対象作業の仕様に従って確認する。

## 作業終了

PRの状態と未コミット変更を確認する。worktreeはマージ済み、または作業を破棄する明示指示があり、必要な変更が保存されていることを確認してから`git worktree remove`で片付ける。`--force`で変更を捨てない。未マージのPRのブランチとworktreeは保持する。
