# エージェントの共通方針

専門性の正本は `.codex/agents/*.toml` とし、役割一覧を別文書へ転記しない。

親は関連Issueと仕様から目的・範囲・受け入れ条件・未決定事項を整理し、担当の成果物を統合する。判断はIssueへ、現在有効な制約は該当ルールへ反映する。

委譲と成果物の受け渡しには [kizuki-agent-handoff](../../.agents/skills/kizuki-agent-handoff/SKILL.md)、リスクに応じた設計・実装の独立確認には [kizuki-review](../../.agents/skills/kizuki-review/SKILL.md) を使う。実装は [TDD方針](../rules/testing/AGENTS.md)、作業場所・反映先は [GitHub運用](../rules/github/AGENTS.md) に従う。

親は成果物・検証結果・未解決事項を報告する。レビュー通過をテスト成功の代わりにしない。
