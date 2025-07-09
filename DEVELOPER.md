# 開発者ガイド - Snowflake MCP Server

このドキュメントは、Snowflake MCP Serverの開発に貢献したい開発者向けのガイドです。

## 🏗️ アーキテクチャ

### プロジェクト構造

```
snowflake-mcp-server/
├── src/snowflake_mcp/
│   ├── __init__.py          # パッケージ初期化
│   ├── __main__.py          # エントリーポイント（FastMCP直接利用）
│   ├── server.py            # MCPサーバー実装（クラスベース）
│   ├── connection.py        # Snowflake接続管理
│   └── query_validator.py   # クエリ検証ロジック
├── tests/
│   ├── test_server.py       # サーバーのテスト
│   ├── test_connection.py   # 接続管理のテスト
│   └── test_query_validator.py # クエリ検証のテスト
├── Claude.md               # プロジェクト開発ガイドライン
├── python_guideline.md     # Python開発ガイドライン  
├── README.md               # ユーザー向けガイド
├── DEVELOPER.md            # 開発者向けガイド（このファイル）
└── pyproject.toml          # 依存関係とプロジェクト設定
```

### 主要コンポーネント

#### 1. QueryValidator (`query_validator.py`)
- **責務**: SQLクエリが読み取り専用かどうかを判定
- **実装**: ホワイトリスト方式（SELECT, SHOW, DESCRIBE, DESC, EXPLAIN）
- **特徴**: 大文字小文字を区別しない、前後の空白を処理

#### 2. SnowflakeConnection (`connection.py`)
- **責務**: Snowflakeデータベースへの接続とクエリ実行
- **認証**: キーペア認証とOAuth認証に対応
- **接続管理**: 遅延接続、適切なリソース管理

#### 3. SnowflakeMCPServer (`server.py`)
- **責務**: MCPプロトコルの実装とツール提供
- **ツール**: query, list_tables, describe_table, get_schema
- **エラーハンドリング**: 適切な例外処理とメッセージ

#### 4. FastMCP直接実装 (`__main__.py`)
- **責務**: シンプルなサーバー起動
- **特徴**: クラスを使わない直接的なアプローチ

## 🧪 テスト戦略

### TDD（Test-Driven Development）

このプロジェクトは和田卓人さんの提唱するTDDアプローチを採用しています：

#### Red-Green-Refactorサイクル

1. **Red**: 失敗するテストを作成
2. **Green**: 最小限の実装でテストを通す
3. **Refactor**: コードを改善する

### テスト実行

```bash
# 全テスト実行
uv run --frozen pytest tests/ -v

# 特定のテストファイル
uv run --frozen pytest tests/test_query_validator.py -v

# 特定のテストメソッド
uv run --frozen pytest tests/test_query_validator.py::TestQueryValidator::test_select_query_is_read_only -v

# カバレッジ付きテスト
uv run --frozen pytest --cov=src/snowflake_mcp --cov-report=term-missing

# 失敗時停止
uv run --frozen pytest -x

# 前回失敗したテストのみ
uv run --frozen pytest --lf
```

### モックとテスト設計

#### Given-When-Then パターン
```python
def test_select_query_is_read_only():
    # Given: 前提条件
    validator = QueryValidator()
    query = "SELECT * FROM users"

    # When: 実行
    result = validator.is_read_only(query)

    # Then: 検証
    assert result is True
```

#### 非同期テストパターン
```python
def test_execute_query_connects_if_not_connected():
    # anyio.run() を使用してasync関数をテスト
    async def run_test():
        return await connection.execute_query("SELECT 1")

    result = anyio.run(run_test)
    assert result == expected_results
```

## 🔧 開発環境セットアップ

### 1. 依存関係のインストール

```bash
# 開発依存関係を含む全依存関係をインストール
uv sync

# 本番依存関係のみ
uv sync --no-dev
```

### 2. 開発用ツール

```bash
# コードフォーマット
uv run --frozen ruff format .

# リント
uv run --frozen ruff check .

# リント修正
uv run --frozen ruff check . --fix

# 型チェック
uv run --frozen pyright
```

### 3. pre-commitフック（オプション）

```bash
# pre-commitの設定
uv run --frozen pre-commit install

# 手動実行
uv run --frozen pre-commit run --all-files
```

## 📦 依存関係管理

### 本番依存関係
- `mcp>=1.10.1`: Model Context Protocol実装
- `snowflake-connector-python>=3.16.0`: Snowflake接続
- `cryptography>=45.0.5`: キーペア認証

### 開発依存関係
- `pytest>=8.4.1`: テストフレームワーク
- `pytest-asyncio>=1.0.0`: 非同期テスト
- `anyio>=4.9.0`: 非同期ランタイム
- `ruff>=0.12.2`: フォーマット・リント
- `pyright>=1.1.402`: 型チェック
- `pre-commit>=4.2.0`: Gitフック管理

### 依存関係の追加

```bash
# 本番依存関係
uv add package-name

# 開発依存関係  
uv add --dev package-name

# 特定バージョン
uv add "package-name>=1.0.0"
```

## 🚀 新機能開発

### 1. 新しいツールの追加

1. **テストファーストで実装**:
   ```python
   # tests/test_server.py に追加
   def test_new_tool_functionality():
       # Given-When-Then でテスト作成
       pass
   ```

2. **実装**:
   ```python
   # __main__.py または server.py に追加
   @mcp.tool()
   async def new_tool(param: str) -> List[Dict[str, Any]]:
       """新しいツールの説明"""
       # 実装
       pass
   ```

3. **テスト確認**:
   ```bash
   uv run --frozen pytest tests/test_server.py::test_new_tool_functionality -v
   ```

### 2. 認証方式の追加

1. **SnowflakeConnection** に新しい認証メソッドを追加
2. **環境変数の設定** を更新
3. **テストの追加** でカバレッジを確保
4. **ドキュメントの更新**

## 🎯 コード品質ガイドライン

### 型ヒント
```python
# 全ての関数に型ヒントを追加
def process_query(query: str) -> List[Dict[str, Any]]:
    pass

# Optionalの使用
from typing import Optional
def connect(self) -> Optional[SnowflakeConnection]:
    pass
```

### docstring
```python
def execute_query(self, query: str) -> List[Dict[str, Any]]:
    """Execute a SQL query and return results.

    Args:
        query: SQL query string to execute

    Returns:
        List[Dict[str, Any]]: Query results as list of dictionaries

    Raises:
        RuntimeError: If query execution fails
    """
```

### エラーハンドリング
```python
# 具体的な例外を発生
if not self._is_read_only_query(sql):
    raise ValueError("Only read-only queries are allowed")

# 元の例外情報を保持
except Exception as e:
    raise RuntimeError(f"Query execution failed: {str(e)}")
```

## 🔍 デバッグ

### ログ出力
```python
import logging

# 開発時のデバッグ
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# コード内でのデバッグ
logger.debug(f"Executing query: {query}")
```

### テストでのデバッグ
```bash
# 詳細出力
uv run --frozen pytest tests/ -v -s

# 特定のテストでブレークポイント
# テストコード内で import pdb; pdb.set_trace()
```

## 📋 リリース手順

### 1. バージョン更新
```bash
# pyproject.toml と __init__.py のバージョンを更新
```

### 2. テスト実行
```bash
# 全テストの実行
uv run --frozen pytest tests/ -v

# コード品質チェック
uv run --frozen ruff check .
uv run --frozen ruff format .
uv run --frozen pyright
```

### 3. ドキュメント更新
- README.md の更新
- DEVELOPER.md の更新
- CHANGELOG.md の追加（必要に応じて）

## 🤝 貢献ガイドライン

### プルリクエスト

1. **ブランチ作成**: `feature/new-feature` または `fix/bug-fix`
2. **TDDで開発**: テストファーストで実装
3. **コード品質**: ruff、pyrightでチェック
4. **テストカバレッジ**: 新機能は100%カバー
5. **ドキュメント**: 必要に応じて更新

### コミットメッセージ
```
feat: 新機能の追加
fix: バグ修正
docs: ドキュメント更新
test: テスト追加・修正
refactor: リファクタリング
```

## 🔧 トラブルシューティング

### 開発環境の問題

**import エラー**:
```bash
# パッケージの再インストール
uv sync --refresh
```

**テストが通らない**:
```bash
# キャッシュクリア
uv run --frozen pytest --cache-clear
```

**型チェックエラー**:
```bash
# pyrightの設定確認
uv run --frozen pyright --stats
```

### MCPサーバーの問題

**接続エラー**:
1. FastMCPのバージョン確認
2. asyncioループの競合確認
3. STDIO設定の確認

## 📚 参考資料

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Snowflake Python Connector](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector)
- [FastMCP Documentation](https://modelcontextprotocol.io/)

---

質問やサポートが必要な場合は、Issueを作成するか、メンテナーにお問い合わせください。
