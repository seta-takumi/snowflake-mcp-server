# Snowflake MCP Server

SnowflakeデータベースとClaude（MCP対応クライアント）を安全に接続するためのModel Context Protocol (MCP) サーバーです。

## 🚀 特徴

- **安全な読み取り専用アクセス**: SELECT、SHOW、DESCRIBE、EXPLAINクエリのみ実行可能
- **セキュアな認証**: キーペア認証とOAuth認証に対応
- **Claude統合**: Claude DesktopやClaude Codeから直接利用可能
- **包括的ツール**: テーブル一覧、スキーマ情報、クエリ実行をサポート

## 📋 前提条件

- Python 3.12以上
- [uv](https://docs.astral.sh/uv/) パッケージマネージャー
- Snowflakeアカウントと適切な権限

## 🔧 インストール
```bash
# GitHubから直接インストール
uv tool install git+https://github.com/seta-takumi/snowflake-mcp-server.git

# ローカルからインストール
git clone https://github.com/seta-takumi/snowflake-mcp-server.git
cd snowflake-mcp-server
uv tool install .
```

## 🔐 認証設定

### キーペア認証（推奨）

#### 1. 秘密鍵・公開鍵の生成

```bash
# 秘密鍵を生成
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

# 公開鍵を生成
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub

# ファイル権限を設定
chmod 600 rsa_key.p8
chmod 644 rsa_key.pub
```

#### 2. Snowflakeユーザーに公開鍵を設定

```sql
-- Snowflakeで実行
ALTER USER your_username SET RSA_PUBLIC_KEY='<公開鍵の内容（-----BEGIN/END部分を除く）>';
```

### OAuth認証（オプション）

企業環境でSSO統合が必要な場合に使用します。詳細は[Snowflake OAuth設定ガイド](https://docs.snowflake.com/en/user-guide/oauth)を参照してください。

## ⚙️ 設定

### connections.toml ファイル（推奨）

Snowflake Python Connectorのネイティブサポートを活用した設定方法です。

#### 1. 設定ファイルの作成

以下の場所にファイルを作成：
- `~/.snowflake/connections.toml`
- `~/.config/snowflake/connections.toml` (Linux)
- `$SNOWFLAKE_HOME/connections.toml` (環境変数で指定)

#### 2. 設定内容

```toml
[myconnection]
account = "your-account"
user = "your-username"
database = "your-database"
schema = "your-schema"
warehouse = "your-warehouse"
role = "your-role"

# キーペア認証の場合
private_key_file = "/path/to/rsa_key.p8"
private_key_file_pwd = ""  # パスフレーズがある場合のみ

# または OAuth認証の場合
# token = "your-oauth-token"
# authenticator = "oauth"
```

### 環境変数での設定（従来方法）

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
export SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=""  # パスフレーズがある場合のみ

# または OAuth認証
export SNOWFLAKE_OAUTH_TOKEN="your-oauth-token"
```

## 🚀 起動方法

### uv toolでインストール後

```bash
# connections.tomlの接続設定を使用
uvx snowflake-mcp-server --connection-name myconnection

# 短縮形
uvx snowflake-mcp-server -c myconnection

# 環境変数を使用する場合
uvx snowflake-mcp-server

# ヘルプの表示
uvx snowflake-mcp-server --help
```

### 開発環境での実行

```bash
# connections.tomlの接続設定を使用
uv run python -m snowflake_mcp_server --connection-name myconnection

# 環境変数を使用する場合
uv run python -m snowflake_mcp_server
```

## 🖥️ Claude Codeでの利用

### 1. 設定ファイルの編集
用途によってそれぞれのファイルで設定を追加します。
- システム全体での設定： `~/.claude.json`
- プロジェクトごとの設定：プロジェクトディレクトリ内で `.mcp.json`

#### uv toolでインストール後（推奨）

```json
"mcpServers": {
  "snowflake-mcp-server": {
    "command": "uvx",
    "args": [
      "snowflake-mcp-server",
      "--connection-name",
      "myconnection"
    ]
  }
}
```

#### 環境変数を使用する場合
```json
"mcpServers": {
  "snowflake-mcp-server": {
    "command": "uvx",
    "args": [
      "snowflake-mcp-server"
    ],
    "env": {
      "SNOWFLAKE_ACCOUNT": "your-account",
      "SNOWFLAKE_USER": "your-username",
      "SNOWFLAKE_DATABASE": "your-database",
      "SNOWFLAKE_SCHEMA": "your-schema",
      "SNOWFLAKE_WAREHOUSE": "your-warehouse",
      "SNOWFLAKE_ROLE": "your-role",
      "SNOWFLAKE_PRIVATE_KEY_PATH": "/path/to/rsa_key.p8"
    }
  }
}
```

#### 開発環境での設定

```json
"mcpServers": {
  "snowflake-mcp": {
    "command": "path/to/uv",
    "args": [
      "--directory",
      "/path/to/snowflake-mcp-server",
      "run",
      "python",
      "-m",
      "snowflake_mcp_server",
      "--connection-name",
      "myconnection"
    ]
  }
}
```

**注意**: uvのパスを確認するには `which uv` を実行してください。

### 2. Claude Codeの再起動

設定を反映するためにClaude Codeを再起動してください。

## 🛠️ 利用可能なツール

### `query`
```
SQLクエリを実行します（読み取り専用）
パラメータ: sql (string) - 実行するSQLクエリ
例: SELECT * FROM customers LIMIT 10
```

### `list_tables`
```
現在のスキーマ内のテーブル一覧を取得します
パラメータ: なし
```

### `describe_table`
```
指定したテーブルの構造を取得します
パラメータ: table_name (string) - テーブル名
例: customers
```

### `get_schema`
```
現在のスキーマ情報を取得します
パラメータ: なし
```

## 📝 使用例

Claude Codeで以下のようにお試しください：

```
現在のデータベースにあるテーブルを教えてください
```

```
customers テーブルの構造を確認してください
```

```
売上データの上位10件を表示してください
SELECT * FROM sales ORDER BY amount DESC LIMIT 10
```

## 🔒 セキュリティ機能

- **読み取り専用制限**: INSERT、UPDATE、DELETE、CREATE、DROPなどの書き込み操作は完全にブロック
- **SQLインジェクション対策**: パラメータ化クエリによる安全な実行
- **認証情報の保護**: 環境変数による秘密情報の管理
- **接続の安全性**: Snowflakeの標準セキュリティプロトコルを使用

## 🚨 トラブルシューティング

### 接続エラー

**症状**: 「Query execution failed: Connection error」
**解決方法**:
1. 環境変数が正しく設定されているか確認
2. Snowflakeアカウント情報の確認
3. 秘密鍵ファイルのパスと権限を確認
4. ネットワーク接続の確認

### 権限エラー

**症状**: 「Access denied」または「Permission denied」
**解決方法**:
1. Snowflakeユーザーのロール権限を確認
2. データベース・スキーマへのアクセス権限を確認
3. ウェアハウスの使用権限を確認

### キーペア認証エラー

**症状**: 「Private key authentication failed」
**解決方法**:
1. 公開鍵がSnowflakeユーザーに正しく設定されているか確認
2. 秘密鍵ファイルの形式とパスフレーズを確認
3. ファイル権限（600）を確認

## 📚 関連リンク

- [Model Context Protocol (MCP) 公式ドキュメント](https://modelcontextprotocol.io/)
- [Snowflake公式ドキュメント](https://docs.snowflake.com/)
- [Claude Code ドキュメント](https://docs.anthropic.com/claude/docs/claude-code)
- [uv パッケージマネージャー](https://docs.astral.sh/uv/)

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 貢献

開発者向けの詳細なガイドは[DEVELOPER.md](./DEVELOPER.md)をご覧ください。

---

**注意**: このツールは読み取り専用アクセスを提供し、データの変更はできません。本番環境での使用前に、適切なアクセス制御とセキュリティ設定を確認してください。
