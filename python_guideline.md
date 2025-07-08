# Python 開発ガイドライン

このドキュメントには、このコードベースでの作業に関する重要な情報が含まれています。これらのガイドラインに正確に従ってください。

## 基本的な開発ルール

1. パッケージ管理

   - uv のみを使用し、pip は絶対に使わない
   - インストール: `uv add package`
   - ツール実行: `uv run tool`
   - アップグレード: `uv add --dev package --upgrade-package package`
   - 禁止事項: `uv pip install`、`@latest`構文

2. コード品質

   - すべてのコードで型ヒントが必須
   - パブリック API には必ず docstring を記述
   - 関数は焦点を絞って小さく保つ
   - 既存のパターンに正確に従う
   - 行の長さ: 最大 88 文字

3. テスト要件
   - フレームワーク: `uv run --frozen pytest`
   - 非同期テスト: asyncio ではなく anyio を使用
   - カバレッジ: エッジケースとエラーをテスト
   - 新機能にはテストが必要
   - バグ修正にはリグレッションテストが必要

- ユーザーレポートに基づくバグ修正や機能追加のコミットには以下を追加:

  ```bash
  git commit --trailer "Reported-by:<name>"
  ```

  `<name>`はユーザーの名前です。

- Github イシューに関連するコミットには以下を追加:
  ```bash
  git commit --trailer "Github-Issue:#<number>"
  ```
- `co-authored-by`や類似の記述を絶対に言及しない。特に、コミットメッセージや PR の作成に使用されたツールについて言及しない。

## プルリクエスト

- 変更内容の詳細なメッセージを作成する。解決しようとする問題の高レベルな説明と、その解決方法に焦点を当てる。明確性を追加しない限り、コードの具体的な詳細には言及しない。

- 常に`jerome3o-anthropic`と`jspahrsummers`をレビュアーとして追加する。

- `co-authored-by`や類似の記述を絶対に言及しない。特に、コミットメッセージや PR の作成に使用されたツールについて言及しない。

## Python ツール

## コードフォーマット

1. Ruff

   - フォーマット: `uv run --frozen ruff format .`
   - チェック: `uv run --frozen ruff check .`
   - 修正: `uv run --frozen ruff check . --fix`
   - 重要な問題:
     - 行の長さ（88 文字）
     - インポートソート（I001）
     - 未使用のインポート
   - 行の折り返し:
     - 文字列: 括弧を使用
     - 関数呼び出し: 適切なインデントで複数行
     - インポート: 複数行に分割

2. 型チェック

   - ツール: `uv run --frozen pyright`
   - 要件:
     - Optional の明示的な None チェック
     - 文字列の型絞り込み
     - チェックが通れば、バージョン警告は無視可能

3. Pre-commit
   - 設定: `.pre-commit-config.yaml`
   - 実行: git commit で実行
   - ツール: Prettier（YAML/JSON）、Ruff（Python）
   - Ruff アップデート:
     - PyPI バージョンをチェック
     - 設定の rev を更新
     - 設定を最初にコミット

## エラー解決

1. CI 失敗

   - 修正順序:
     1. フォーマット
     2. 型エラー
     3. リンティング
   - 型エラー:
     - 完全な行コンテキストを取得
     - Optional 型をチェック
     - 型絞り込みを追加
     - 関数シグネチャを確認

2. 一般的な問題

   - 行の長さ:
     - 括弧で文字列を分割
     - 複数行の関数呼び出し
     - インポートを分割
   - 型:
     - None チェックを追加
     - 文字列型を絞り込み
     - 既存のパターンに合わせる
   - Pytest:
     - テストが anyio pytest マークを見つけられない場合、pytest 実行コマンドの最初に PYTEST_DISABLE_PLUGIN_AUTOLOAD=""を追加してみる:
       `PYTEST_DISABLE_PLUGIN_AUTOLOAD="" uv run --frozen pytest`

3. ベストプラクティス
   - コミット前に git status をチェック
   - 型チェック前にフォーマッターを実行
   - 変更を最小限に保つ
   - 既存のパターンに従う
   - パブリック API を文書化
   - 徹底的にテスト
