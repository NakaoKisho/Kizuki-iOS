# 文書・Issue・Figmaの運用

## 文書を書くとき

[記載基準](writing-policy.md)に従い、今後の行動を決める制約と必要な手順を簡潔に残す。1文書1主題とし、入口から必要な補助資料・テンプレート・スクリプトへリンクする。同じ内容を複数箇所で管理しない。

## GitHub Issues

要求・受け入れ条件・設計判断の経緯はIssueに残す。ADRファイルは別途作らない。

新規Issueは [kizuki-issue](../../../.agents/skills/kizuki-issue/SKILL.md) で生成・検証・作成する。手順・テンプレート・CLIはスキル内を正本とする。

決定を変更する場合は新Issueから旧Issueを参照し、旧Issueにも後継へのリンクを残す。経緯をルール文書へ転記せず、現在有効な指示を更新する。ブランチ・PRの扱いは[GitHub運用](../github/AGENTS.md)に従う。

## Figma

デザインの正本は [Kizukiの共通Figma](https://www.figma.com/design/a2cHMzgean8SHB7o8LaTZO/Kizuki?node-id=0-1) とし、Android版とiOS版で同じファイルを使用する。実装はプラットフォームごとに行い、このリポジトリではiOS版を扱う。

画面・操作フロー・コンポーネントと、未記録・空・入力途中など必要な表示状態を管理する。関連Issueには対象フレーム・ノードのリンクを記載する。判断理由はIssueに残す。

## 更新時の確認

リンク、仕様間の整合、未実装機能を実装済みと書いていないかを確認する。仕様変更に伴うIssue・Figma・実装の更新要否も確認する。
