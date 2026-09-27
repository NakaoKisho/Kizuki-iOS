# Kizuki iOS

Kizukiは「なんとなくの不調」や「体調の変化」を簡単に記録し、振り返るためのiOSアプリです。記録をグラフと短い文章にまとめ、受診時に医師へ提示・読み上げできるレポートを目指します。

FigmaでUI・UXを検討し、架空データで操作できるUIモックから開発します。振る舞いを変える実装はTDDで進めます。

## 現在の段階

Android版と対応する開発方針、Issue・レビュー・Git運用の土台を整備しています。初期構成は[プロダクト方針](.codex/rules/product/AGENTS.md)で定め、採用理由は[判断Issue](https://github.com/NakaoKisho/Kizuki-iOS/issues/1)に記録しています。Xcodeプロジェクトは未作成で、アプリの実装・実行検証は次の段階です。

## 開発環境

開発補助スクリプトと全テストにはPython 3.11以上、GitHub操作には認証済みのGitHub CLIが必要です。`python3 --version`で確認し、古いPythonが選ばれる場合はPython 3.11以上の環境を有効にするか、記載コマンドの`python3`をインストール済みの`python3.14`等に置き換えてください。

iOSアプリのビルド、テスト、Simulator操作には[完全版XcodeとXcode付属のコマンドラインツール](https://developer.apple.com/documentation/xcode/xcode-command-line-tool-reference)を使用します。standaloneのCommand Line Tools for Xcodeだけでは`xcodebuild`や`simctl`を含むiOS開発環境になりません。

Xcodeをインストールして利用規約と初回セットアップを完了した後、次のコマンドで選択中のDeveloper Directoryと利用可能なツールを確認します。

```bash
xcode-select --print-path
xcodebuild -version
xcrun simctl list devices available
```

`xcode-select --print-path`が`/Library/Developer/CommandLineTools`を示す場合は、XcodeのSettings > Locations > Command Line Toolsで使用するXcodeを選択するか、Appleの案内に従ってDeveloper Directoryを切り替えます。

既定の設定を変えずに実行する場合は、各コマンドに`DEVELOPER_DIR`を指定できます。次はXcodeを標準の場所にインストールした場合の例です。実際の配置先に合わせて変更してください。

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -version
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcodebuild -showsdks
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun simctl list devices available
```

開発時は[AGENTS.md](AGENTS.md)から必要なルールを確認してください。Issueの作成は[Issueスキル](.agents/skills/kizuki-issue/SKILL.md)、作業開始と直接push防止は[GitHub運用](.codex/rules/github/AGENTS.md)に従います。

サブエージェントは[委譲・成果物の手順](.codex/agents/AGENTS.md)を使います。Codexのプロジェクトhookは、クライアントの`/hooks`等で定義を確認して信頼した後に動作します。ファイルを置くだけで有効化済みとは扱わないでください。
