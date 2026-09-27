---
name: kizuki-review
description: Kizukiのレビュー計画、リスク判定、観点の割当、再レビュー、受入を調整するときに使用する。設計・実装レビューの共通規約を提供する。
---

# レビューの調整

親とレビュー担当は [判定と受入](references/policy.md) と [固定観点](references/checklist.md) を読む。プロダクトの仕様・画面・集計・レポートを扱う場合は [製品確認項目](references/product-checks.md) も読む。

- 設計案の作成・レビューには [kizuki-design-review](../kizuki-design-review/SKILL.md) を使う。
- 実装・文書・設定の差分と検証記録のレビューには [kizuki-implementation-review](../kizuki-implementation-review/SKILL.md) を使う。

工程スキルから共通規約を参照したときは、同じスキルを再帰的に呼び直さず、その工程を続ける。

## 担当の選び方

役割名の固定表を作らず、`.codex/agents/*.toml` のdescriptionと専門性を基に選ぶ。適用するV01〜V14の担当と、該当しない項目の理由を今回のレビュー記録に残す。UI・Figmaには視覚・操作面、Git・hook・CIには開発運用面の専門性を含める。

medium・highでは複数の独立担当へ同じ版を渡し、全適用観点を網羅する。初回判定前に他担当の結論を渡さない。作者自身の担当箇所の確認を独立レビューに数えない。

## 報告と受入

[kizuki-agent-handoff](../kizuki-agent-handoff/SKILL.md) でprepare・報告・checkを行う。担当のevidenceに観点別の判定・根拠・検証不足を、findingsに未解消指摘を記録する。親はcheckだけで完了とせず、受け入れ条件と判定規約も照合する。

関連IssueまたはPRへ対象版・リスク・担当観点・指摘対応・検証結果を要約する。詳細ログをルールへ蓄積しない。
