# Snowflake MCP Server

Claude Codeを使用してSnowflake MCP (Model Context Protocol) サーバーを開発するためのガイドです。

## プロジェクト概要

このプロジェクトは、SnowflakeデータベースとMCPクライアント（Claude等）を接続するサーバーです。SQLクエリの実行、スキーマの取得、テーブル情報の参照などの機能を提供します。

## 開発環境

- Python 3.11+
- uv (パッケージマネージャー)
- MCP SDK
- Snowflake Connector for Python

## セットアップ

### 1. 依存関係のインストール

```bash
# 基本依存関係
uv add mcp
uv add snowflake-connector-python
uv add cryptography  # キーペア認証用

# OAuth認証を使用する場合
uv add requests  # OAuth フロー用

# 開発用依存関係
uv add --dev pytest pytest-asyncio anyio ruff pyright pre-commit
```

### 2. セキュアな認証設定

#### キーペア認証（推奨）

```bash
# 秘密鍵を生成
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

# 公開鍵を生成
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub

# Snowflakeユーザーに公開鍵を設定
# ALTER USER your_username SET RSA_PUBLIC_KEY='<公開鍵の内容>';
```

環境変数の設定：

```bash
# 基本設定
export SNOWFLAKE_ACCOUNT="your-account"
export SNOWFLAKE_USER="your-username"
export SNOWFLAKE_DATABASE="your-database"
export SNOWFLAKE_SCHEMA="your-schema"
export SNOWFLAKE_WAREHOUSE="your-warehouse"
export SNOWFLAKE_ROLE="your-role"

# キーペア認証
export SNOWFLAKE_PRIVATE_KEY_PATH="/path/to/rsa_key.p8"
export SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=""  # パスフレーズがある場合

# または、OAuth認証
export SNOWFLAKE_OAUTH_TOKEN="your-oauth-token"
```

#### OAuth認証（オプション）

```bash
# OAuth用設定
export SNOWFLAKE_OAUTH_CLIENT_ID="your-client-id"
export SNOWFLAKE_OAUTH_CLIENT_SECRET="your-client-secret"
export SNOWFLAKE_OAUTH_REDIRECT_URI="http://localhost:8080/callback"
```

## 主要機能

### 1. 接続管理 (`connection.py`)

- Snowflakeへの接続とセッション管理
- 接続プールの管理
- エラーハンドリング

### 2. MCP サーバー (`server.py`)

- MCPプロトコルの実装
- セキュアな認証（キーペア、OAuth）
- 以下のツールを提供：
  - `query`: SQLクエリの実行
  - `list_tables`: テーブル一覧の取得
  - `describe_table`: テーブル構造の取得
  - `get_schema`: スキーマ情報の取得

### 3. 認証管理 (`auth.py`)

- キーペア認証の実装
- OAuth認証フローの管理
- 認証情報の安全な管理

### 4. セキュリティ

- 読み取り専用クエリの制限
- SQLインジェクション対策
- 接続情報の安全な管理

## 開発ガイドライン

### TDD（Test-Driven Development）- 和田卓人(t-wada)アプローチ

このプロジェクトは和田卓人さんが提唱するTDDの原則に従って開発します。

#### TDDの心構え

**「動作するきれいなコード」を書くための手法**
- テストは仕様書であり、設計の道具
- 小さなステップで確実に進む
- リファクタリングで設計を改善し続ける

#### TDDサイクル（Red-Green-Refactor）

**1. Red**: 失敗するテストを書く
- 「何を作るか」を明確にするためのテスト
- 最初は必ず失敗させる（テストが正しく動作することを確認）
- 一つの振る舞いに対して一つのテスト

**2. Green**: とにかくテストを通す
- 最短距離でテストを通すコードを書く
- 「正しく動く」ことを最優先（きれいさは後）
- 仮実装、明白な実装、三角測量を使い分ける

**3. Refactor**: テストを保ったままコードを改善
- 重複排除と意図の明確化
- テストコードもリファクタリング対象
- 「動作する」を保ったまま「きれい」にする

#### TDD開発の指針

**仮実装 → 三角測量 → 明白な実装**

```python
# 1. 仮実装: とにかくテストを通す
def add(a, b):
    return 3  # テストで期待値が3の場合

# 2. 三角測量: 複数のテストで一般化を促す
def add(a, b):
    if a == 1 and b == 2:
        return 3
    if a == 2 and b == 3:
        return 5
    return 0

# 3. 明白な実装: 正しい実装が明らかになったら一気に書く
def add(a, b):
    return a + b
```

**TODOリスト駆動開発**
- 実装すべき機能をTODOリストに書き出す
- 一つずつテストにしていく
- 完了したらリストから消す

#### テスト設計の原則

**良いテストの条件（FIRST原則）**
- **Fast**: 高速に実行できる
- **Independent**: 他のテストに依存しない
- **Repeatable**: 繰り返し実行できる
- **Self-Validating**: 成功/失敗が明確
- **Timely**: 適切なタイミングで書かれている

**Given-When-Then パターン**
```python
def test_snowflake_query_execution():
    # Given: 前提条件
    connection = SnowflakeConnection()
    query = "SELECT 1"
    
    # When: 実行
    result = await connection.execute_query(query)
    
    # Then: 検証
    assert len(result) == 1
```

### コード品質

- 全ての関数に型ヒントを追加
- パブリックAPIにはdocstringを記述
- 最大行長: 88文字
- 既存のパターンに従う
- テストファーストで開発

### テスト

- フレームワーク: pytest
- 非同期テスト: anyio使用
- モック: pytest-mock
- カバレッジ: pytest-cov
- 実行: `uv run --frozen pytest`

### コードフォーマット

```bash
# フォーマット
uv run --frozen ruff format .

# チェック
uv run --frozen ruff check .

# 修正
uv run --frozen ruff check . --fix

# 型チェック
uv run --frozen pyright
```

## 実装例

### 基本的なMCPサーバー構造

```python
from typing import Any, Dict, List, Optional
import asyncio
import os
import re
from mcp.server import Server
from mcp.types import Tool, TextContent
from .connection import SnowflakeConnection

class SnowflakeMCPServer:
    def __init__(self):
        self.connection = SnowflakeConnection()
        self.server = Server("snowflake-mcp")
        self._setup_tools()
    
    def _is_read_only_query(self, query: str) -> bool:
        """クエリが読み取り専用かチェック"""
        query_upper = query.strip().upper()
        allowed_statements = ['SELECT', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN']
        return any(query_upper.startswith(stmt) for stmt in allowed_statements)
    
    def _setup_tools(self) -> None:
        """MCPツールの設定"""
        @self.server.tool(
            name="query",
            description="Execute read-only SQL queries on Snowflake"
        )
        async def query(sql: str) -> List[TextContent]:
            if not self._is_read_only_query(sql):
                return [TextContent(
                    type="text",
                    text="Error: Only read-only queries are allowed"
                )]
            
            try:
                results = await self.connection.execute_query(sql)
                return [TextContent(
                    type="text",
                    text=f"Query executed successfully. Results: {results}"
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Query execution failed: {str(e)}"
                )]
    
    async def run(self) -> None:
        """サーバーの実行"""
        await self.server.run()
```

### 接続管理クラス

```python
import os
from typing import Any, Dict, List, Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs8
import snowflake.connector

class SnowflakeConnection:
    def __init__(self):
        self.connection: Optional[snowflake.connector.SnowflakeConnection] = None
    
    def _get_connection_params(self) -> Dict[str, Any]:
        """セキュアな接続パラメータの取得"""
        params = {
            'account': os.getenv('SNOWFLAKE_ACCOUNT'),
            'user': os.getenv('SNOWFLAKE_USER'),
            'database': os.getenv('SNOWFLAKE_DATABASE'),
            'schema': os.getenv('SNOWFLAKE_SCHEMA'),
            'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
            'role': os.getenv('SNOWFLAKE_ROLE'),
        }
        
        # キーペア認証
        private_key_path = os.getenv('SNOWFLAKE_PRIVATE_KEY_PATH')
        if private_key_path:
            with open(private_key_path, 'rb') as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=os.getenv('SNOWFLAKE_PRIVATE_KEY_PASSPHRASE', '').encode() or None,
                )
            
            pkb = private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            params['private_key'] = pkb
        
        # OAuth認証（代替）
        oauth_token = os.getenv('SNOWFLAKE_OAUTH_TOKEN')
        if oauth_token:
            params['token'] = oauth_token
            params['authenticator'] = 'oauth'
        
        return params
    
    async def connect(self) -> None:
        """Snowflakeに接続"""
        connection_params = self._get_connection_params()
        self.connection = snowflake.connector.connect(**connection_params)
    
    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """SQLクエリの実行"""
        if not self.connection:
            await self.connect()
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cursor.close()
    
    async def close(self) -> None:
        """接続のクローズ"""
        if self.connection:
            self.connection.close()
            self.connection = None
```

## 使用方法

### 1. サーバーの起動

```bash
uv run python -m snowflake_mcp.server
```

### 2. Claude Codeでの使用

```bash
# MCP設定でサーバーを追加
claude-code --mcp-server snowflake-mcp-server
```

### 3. 利用可能なツール

- `query`: SQLクエリの実行
- `list_tables`: テーブル一覧の取得
- `describe_table`: テーブル構造の取得
- `get_schema`: スキーマ情報の取得

## セキュリティ考慮事項

1. **キーペア認証**: パスワードの代わりに公開鍵暗号化を使用
2. **OAuth認証**: 企業環境での統合認証
3. **読み取り専用**: SELECT、DESCRIBE、SHOW文のみ許可
4. **SQLインジェクション対策**: パラメータ化クエリの使用
5. **秘密鍵管理**: 適切なファイル権限（600）の設定
6. **エラーハンドリング**: 詳細なエラー情報の制限

### 秘密鍵の安全な管理

```bash
# 秘密鍵ファイルの権限設定
chmod 600 /path/to/rsa_key.p8

# 秘密鍵ディレクトリの権限設定
chmod 700 /path/to/keys/
```

## トラブルシューティング

### 接続エラー

- 環境変数の設定を確認
- Snowflakeアカウント情報の確認
- キーペア認証の場合：
  - 秘密鍵ファイルのパスと権限を確認
  - 公開鍵がSnowflakeユーザーに正しく設定されているか確認
  - パスフレーズの設定を確認
- OAuth認証の場合：
  - トークンの有効期限を確認
  - クライアントID・シークレットの設定を確認
- ネットワーク接続の確認

### 権限エラー

- Snowflakeロールの権限を確認
- 必要なスキーマ・テーブルへのアクセス権限を確認

## 開発タスク

### Phase 1: 基本実装（TDD）

**認証機能の開発**
- [ ] 環境変数読み取りのテスト作成→実装
- [ ] 秘密鍵読み込みのテスト作成→実装  
- [ ] キーペア認証のテスト作成→実装
- [ ] 接続エラーハンドリングのテスト作成→実装

**クエリ実行機能の開発**
- [ ] クエリ判定のテスト作成→実装
- [ ] クエリ実行のテスト作成→実装
- [ ] 結果変換のテスト作成→実装
- [ ] エラーハンドリングのテスト作成→実装

**MCPサーバー機能の開発**
- [ ] queryツールのテスト作成→実装
- [ ] レスポンス形式のテスト作成→実装

### Phase 2: 機能拡張（TDD）

**メタデータ取得機能**
- [ ] list_tablesツールのテスト作成→実装
- [ ] describe_tableツールのテスト作成→実装
- [ ] get_schemaツールのテスト作成→実装

**OAuth認証（オプション）**
- [ ] OAuth認証のテスト作成→実装
- [ ] トークン管理のテスト作成→実装

### Phase 3: 最適化（TDD）

**パフォーマンス改善**
- [ ] 接続プールのテスト作成→実装
- [ ] キャッシュ機能のテスト作成→実装
- [ ] 統合テストの作成→実装

## TDDテストコマンド（和田卓人流）

### Red-Green-Refactorサイクル

```bash
# Red: 失敗するテストを書いて実行
uv run --frozen pytest tests/test_query_validator.py::test_select_query_is_read_only -v
# ImportError または NameError で失敗することを確認

# Green: 最小実装でテストを通す
# 実装後...
uv run --frozen pytest tests/test_query_validator.py::test_select_query_is_read_only -v
# ✓ PASSED

# 次のテストを追加してRed状態にする
uv run --frozen pytest tests/test_query_validator.py::test_insert_query_is_not_read_only -v

# Refactor: 設計改善
# リファクタリング後、全テストが通ることを確認
uv run --frozen pytest tests/test_query_validator.py -v
```

### 段階的テスト実行

```bash
# 1. 一つの振る舞いから始める
uv run --frozen pytest tests/test_query_validator.py::test_select_query_is_read_only -v

# 2. 対となるテストを追加
uv run --frozen pytest tests/test_query_validator.py::test_insert_query_is_not_read_only -v

# 3. エッジケースを追加
uv run --frozen pytest tests/test_query_validator.py::test_empty_query_is_not_read_only -v

# 4. クラス全体のテスト
uv run --frozen pytest tests/test_query_validator.py -v

# 5. モジュール全体のテスト
uv run --frozen pytest tests/ -v
```

### カバレッジと品質確認

```bash
# カバレッジ測定
uv run --frozen pytest --cov=src/snowflake_mcp --cov-report=term-missing

# 高速実行（統合テスト除外）
uv run --frozen pytest -m "not integration" -v

# 失敗で停止（問題に集中）
uv run --frozen pytest -x

# 変更したファイルのテストのみ
uv run --frozen pytest --lf
```## 和田卓人流TDDの実践指針

### 1. 小さく始める（ベイビーステップ）

```bash
# 最初は最小のテストから
uv run --frozen pytest tests/test_query_validator.py::test_select_query_is_read_only -v

# 次のテストを追加
uv run --frozen pytest tests/test_query_validator.py::test_insert_query_is_not_read_only -v

# 全体が通ることを確認
uv run --frozen pytest tests/test_query_validator.py -v
```

### 2. リズムを保つ（Red-Green-Refactorの高速サイクル）

```bash
# Red: テストを書いて失敗させる（約1-2分）
# Green: 最小実装でテストを通す（約1-2分）  
# Refactor: 設計を改善する（約1-5分）
# 上記を繰り返す（1サイクル約5-10分）
```

### 3. TODO駆動開発

実装途中で気づいたことをTODOに追加：

```python
# TODO: エラーメッセージを詳細化する
# TODO: SQLコメントを除去してから判定する  
# TODO: 大文字小文字の混在パターンをテストする
# TODO: 空白文字のパターンをテストする
# TODO: 複数行クエリの対応
```

### 4. 設計の改善指標

- **重複の排除**: DRY原則
- **意図の明確化**: 変数名、関数名の改善
- **責任の分離**: 単一責任原則
- **テスタビリティ**: テストしやすい設計

### 5. 実装完了の判断

一つの機能（TODOアイテム）について：
- [ ] 成功ケースのテストが通る
- [ ] 失敗ケースのテストが通る  
- [ ] エッジケースのテストが通る
- [ ] リファクタリングが完了している
- [ ] TODOリストから除去済み

### 6. テストの粒度

**和田卓人さんの推奨する粒度**
```python
# ❌ 粒度が大きすぎる
def test_snowflake_connection():
    # 接続、認証、クエリ実行、結果取得を一度にテスト
    pass

# ✅ 適切な粒度
def test_keypair_auth_params_creation():
    # キーペア認証パラメータの作成のみテスト
    pass

def test_query_execution_with_valid_connection():
    # 有効な接続でのクエリ実行のみテスト
    pass

def test_result_formatting():
    # 結果のフォーマットのみテスト
    pass
```

### 7. モックの使い方

```python
# ❌ 過度なモック
def test_with_too_many_mocks():
    with patch('os.getenv'), \
         patch('snowflake.connector.connect'), \
         patch('cryptography.hazmat.primitives.serialization.load_pem_private_key'), \
         patch('pathlib.Path.open'):
        # テストが何をテストしているか不明
        pass

# ✅ 必要最小限のモック
def test_connection_with_keypair():
    with patch('snowflake.connector.connect') as mock_connect:
        # Snowflake接続のみモック、他は実際の値を使用
        connection = SnowflakeConnection()
        # ...
```

### 8. テストの命名規則

```python
# ✅ 和田卓人流の命名（振る舞いを表現）
def test_select_query_is_recognized_as_read_only():
    pass

def test_insert_query_is_rejected_as_write_operation():
    pass

def test_empty_query_returns_false_for_read_only_check():
    pass

def test_connection_fails_when_private_key_file_not_found():
    pass
```

## 開発時の心構え

### TDDの目的を忘れない

1. **設計の改善**: テストを書くことで設計が良くなる
2. **リファクタリングの安全性**: テストがあることで安心して改善できる
3. **仕様の明確化**: テストが仕様書の役割を果たす
4. **バグの早期発見**: 問題を早く見つけられる

### よくある間違いを避ける

```python
# ❌ テストのためのテスト
def test_method_called():
    mock.assert_called_once()  # 実装の詳細に依存

# ✅ 振る舞いのテスト
def test_read_only_query_returns_results():
    result = connection.execute_query("SELECT 1")
    assert len(result) > 0  # 期待する振る舞いを検証
```

### TDD開発のリズム

```
📝 TODO: 次に実装する機能を決める
🔴 Red: 失敗するテストを書く
🟢 Green: 最小実装でテストを通す
🔵 Refactor: コードを改善する
✅ Done: TODOから除去
↩️ 次のTODOへ
```
