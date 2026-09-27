---
name: kizuki-issue
description: KizukiのGitHub Issue本文を作成・検証・登録するときに使用する。機能・修正と設計判断のテンプレートをCLIで扱う。
---

# Issue作成手順

前提はPython 3.10以上、GitHub CLIのインストールと`gh auth login`による認証。以下はリポジトリルートから実行する。Windowsでは環境に応じて`python3`を`py -3`または`python`に置き換える。本文はUTF-8（BOM付きも可）で保存する。

必須項目は [機能・修正](templates/task.md) と [設計判断](templates/decision.md) のテンプレートを正本とする。

## 生成・記入・検証

機能・修正は`task`、設計判断は`decision`を選ぶ。次は設計判断の例である。出力先はリポジトリ外の作業用ファイルにし、既存ファイルは上書きしない。

```bash
python3 .agents/skills/kizuki-issue/scripts/issue.py init --type decision --output ../kizuki-decision.md
```

生成した本文の各節を記入し、`<!-- TODO: ... -->`をすべて置き換える。該当項目がない場合も「該当なし」と理由を書く。レベル2見出しの追加・削除・並べ替えはせず、補足には各節内の文章やレベル3見出しを使う。

見出しはテンプレートの`##`形式を使う。下線形式の見出しと混同するため、コードブロックの外ではハイフンだけの行を区切り線として使わない。

```bash
python3 .agents/skills/kizuki-issue/scripts/issue.py validate --type decision --body-file ../kizuki-decision.md
```

## GitHubへ作成

本文の意味・採用理由・機密情報と、今回の依頼がGitHubへの作成を含むかを確認する。下書き・検証だけの依頼ではcreateを実行しない。

本文と送信先を確認し、次を実行する。`create`でも同じ検証を行うため、未記入のテンプレートは送信できない。外部への書き込みはこのサブコマンドだけで行う。

```bash
python3 .agents/skills/kizuki-issue/scripts/issue.py create --type decision --title '設計判断: 記録の尺度' --body-file ../kizuki-decision.md
```

内部では、検証済み本文のUTF-8スナップショットを一時ファイルに保存し、次のコマンドを引数配列で実行する。送信先は`github.com/NakaoKisho/Kizuki-iOS`に固定する。`task`ではラベルを指定しない。

```text
gh issue create --repo github.com/NakaoKisho/Kizuki-iOS --title <指定したタイトル> --body-file <検証済み本文の一時ファイル> --label decision
```

成功時はghのIssue URLが出力される。非0で終了した場合は未成功として扱い、出力とGitHub上の作成状況を確認してから再実行する。通信失敗後に重複作成しないよう、自動再試行は行わない。

`decision`ラベルがない場合は、管理者が`gh label create decision --repo github.com/NakaoKisho/Kizuki-iOS --color 7057ff --description '設計判断と採用理由'`で準備する。スクリプトは認証やラベル設定を変更しない。

## スクリプトの検証

```bash
python3 -B -m unittest discover -s .agents/skills/kizuki-issue/scripts/tests -v
```

テストではgh実行を置き換え、実際のIssueを作成しない。テンプレートの必須項目を変える場合は、対応する判断Issue・スクリプトの挙動・テストも確認する。内容の意味や機密情報を機械的に判定するツールではない。
