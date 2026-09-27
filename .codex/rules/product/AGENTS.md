# プロダクトの基本方針

## 目指す体験

1. 体調が悪いときでも、少ない操作で不調や体調変化を記録できる。
2. 自分の記録を時系列で振り返り、変化を視覚的に確認できる。
3. 受診時に、医師へ提示するレポートと読み上げられる文章で経過を伝えられる。

レポートは本人の記録を伝えるためのものとし、診断や原因を断定する表現を加えない。

## 最初の段階

FigmaによるUI・UX設計と、架空データで操作できるiOSのUIモックを対象とする。受診用レポートも初期の検討に含め、伝えたい内容と記録項目の対応を確認する。

UIにはSwiftUIを使用し、Apple Human Interface Guidelinesに沿って設計・実装する。SwiftUIだけで満たせない個別要件についてはUIKit連携を検討できる。

記録項目、尺度、集計、永続化、同期、出力形式、対象iOSバージョン、Bundle ID、テスト構成は未決定である。新しい案は提案として記載し、採用判断はIssueに残す。

## 設計・レビュー

設計の作成・確認には [kizuki-design-review](../../../.agents/skills/kizuki-design-review/SKILL.md)、実装の確認には [kizuki-implementation-review](../../../.agents/skills/kizuki-implementation-review/SKILL.md) を使い、製品確認項目を適用する。
