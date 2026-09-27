# Kizukiの作業方針

## 目的

Kizukiは「なんとなくの不調」「体調変化」を簡単に記録・視覚化し、受診時に医師へ提示・読み上げできるグラフと文章のレポートを作るiOSアプリである。

FigmaでUI・UXを検討し、架空データによるUIモックから詳細機能へ進む。未決定の仕様を確定事項として扱わない。

## 共通方針

- やり取りと文書は日本語を基本とする。
- iOSアプリの作成・開発には完全版Xcodeを使用し、CLI実行にはXcodeに同梱される`xcodebuild`・`xcrun`・`simctl`等を使用する。standaloneのCommand Line ToolsだけでiOSアプリをビルドできると扱わない。
- 振る舞いを変えるコードはTDDで進める。失敗するテストを先に確認し、最小実装とリファクタリングを行う。
- 作業ごとにworktreeを使い、最新の`origin/develop`から分岐する。既存PRの修正はそのworktreeを継続使用する。
- 変更はPRで`作業ブランチ → develop → stg → main`の順に反映する。長期ブランチへの直接pushと保護の迂回は禁止する。
- Codexのサブエージェントを専門性に応じて使う。作者の自己確認を独立レビューと称さない。
- モック・テスト・文書・エージェント出力には架空の体調データを使用する。

## 必要なルールを読む

親エージェントは作業開始時に該当文書を明示的に読み、委譲先にも参照パスを渡す。深い階層のAGENTSが全作業へ自動適用されるとは扱わない。

| 文書 | 読むタイミング |
| --- | --- |
| [product](.codex/rules/product/AGENTS.md) | 要件、UI・UX、記録、集計、レポート |
| [documentation](.codex/rules/documentation/AGENTS.md) | 文書、Issue、Figmaの仕様の作成・更新 |
| [testing](.codex/rules/testing/AGENTS.md) | 実装、修正、リファクタリング、検証 |
| [agents](.codex/agents/AGENTS.md) | 作業全体の調整、専門エージェントの選択と委譲 |
| [レビュー調整スキル](.agents/skills/kizuki-review/SKILL.md) | リスク判定、工程別レビュー、独立確認と受入 |
| [github](.codex/rules/github/AGENTS.md) | worktree、ブランチ、コミット、PR、昇格 |

## 情報の責務

READMEは人向けの入口、ルートAGENTSは共通指示と案内、詳細ルールは継続的な制約、スキルは必要な作業手順、エージェント定義は専門性を扱う。GitHub Issuesに要求・受け入れ条件・判断理由を残し、Figmaに視覚的な仕様を置く。導入背景やコードから明白な情報をルールへ転記しない。

仕様間の矛盾を関連資料と更新履歴で解消できない場合や、記述の要否に迷った場合はユーザーに確認する。
