# プロダクトの基本方針

## 目指す体験

1. 体調が悪いときでも、少ない操作で不調や体調変化を記録できる。
2. 自分の記録を時系列で振り返り、変化を視覚的に確認できる。
3. 受診時に、医師へ提示するレポートと読み上げられる文章で経過を伝えられる。

レポートは本人の記録を伝えるためのものとし、診断や原因を断定する表現を加えない。

## 最初の段階

FigmaによるUI・UX設計と、架空データで操作できるiOSのUIモックを対象とする。受診用レポートも初期の検討に含め、伝えたい内容と記録項目の対応を確認する。

UIにはSwiftUIを使用し、Apple Human Interface Guidelinesに沿って設計・実装する。SwiftUIだけで満たせない個別要件についてはUIKit連携を検討できる。

## 初期構成

- 最低対応OSはiOS 17.0、Bundle IDは`com.vegcale.kizuki`とする。
- 初期UIモックはメモリ内の架空データを使い、再起動で操作結果が消えることを画面にも明示する。永続化はSwiftDataを第一候補として評価し、記録スキーマ・移行・データ保全を検証してから導入する。
- 同期・アカウントは初期モックに導入しない。iCloud・HealthKit・外部サーバー等の連携は、要求が具体化した段階で別途判断する。
- 単体・直接呼び出す統合テストはSwift Testing、UIテストはXCTest/XCUIAutomationを使う。
- 機能別に小さく整理し、必要に応じて状態・計算・保存を分離する。SwiftUIの標準データフローを使い、複雑な状態にはObservationを検討する。全画面へのViewModelや外部アーキテクチャライブラリを一律必須にしない。
- Xcode 26.2で開始し、Swift 6言語モード、共有scheme、通常の`.xcodeproj`管理を採用する。配布時には提出要件に適合するXcodeを確認する。

この方針の決定と実装・登録完了を区別する。プロジェクト作成時に設定を反映し、最低対応OSと新しいOSで検証する。Apple DeveloperでのApp ID登録・Team設定は署名設定時に確認する。

記録項目、尺度、集計、永続化の詳細、出力形式は未決定である。新しい案は提案として記載し、採用判断はIssueに残す。

## 設計・レビュー

設計の作成・確認には [kizuki-design-review](../../../.agents/skills/kizuki-design-review/SKILL.md)、実装の確認には [kizuki-implementation-review](../../../.agents/skills/kizuki-implementation-review/SKILL.md) を使い、製品確認項目を適用する。
