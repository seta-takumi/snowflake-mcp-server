"""Snowflake 接続管理 (関数型スタイル中心)。

従来の OOP クラス `SnowflakeConnection` は互換性のため残しつつ、
実際のロジックは純粋/準純粋なトップレベル関数へ委譲する。
テスト互換性を維持しながら関数型スタイルへ移行しやすくするための段階的リファクタ。
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Mapping, Optional

import snowflake.connector
from cryptography.hazmat.primitives import serialization

# --------------------------------------------------------------------------------------
# 純関数 / ヘルパ
# --------------------------------------------------------------------------------------

EnvMapping = Mapping[str, str | None]


def get_connection_params(env: EnvMapping | None = None) -> Dict[str, Any]:
    """環境変数 (デフォルト: os.environ) から Snowflake 接続パラメータ dict を構築する。

    KeyPair 認証, OAuth を必要に応じて追加。
    可能な限り副作用を小さくするため、ファイル読み込み以外は純粋。

    Returns:
        dict: snowflake.connector.connect(**params) にそのまま渡せるパラメータ。
    """
    env = env or os.environ  # 明示渡しを許容しテスト容易性向上

    params: Dict[str, Any] = {
        "account": env.get("SNOWFLAKE_ACCOUNT"),
        "user": env.get("SNOWFLAKE_USER"),
        "database": env.get("SNOWFLAKE_DATABASE"),
        "schema": env.get("SNOWFLAKE_SCHEMA"),
        "warehouse": env.get("SNOWFLAKE_WAREHOUSE"),
        "role": env.get("SNOWFLAKE_ROLE"),
    }

    private_key_path = env.get("SNOWFLAKE_PRIVATE_KEY_PATH")
    if private_key_path:
        passphrase = env.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
        with open(private_key_path, "rb") as key_file:  # IO (副作用)
            private_key = serialization.load_pem_private_key(
                key_file.read(), password=passphrase.encode() if passphrase else None
            )
        params["private_key"] = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    oauth_token = env.get("SNOWFLAKE_OAUTH_TOKEN")
    if oauth_token:
        params["token"] = oauth_token
        params["authenticator"] = "oauth"

    return params


def open_connection(
    connection_name: str | None = None,
    env: EnvMapping | None = None,
) -> snowflake.connector.SnowflakeConnection:
    """接続を生成して返す (副作用: Snowflake へ接続)。

    Args:
        connection_name: connections.toml のエントリ名 (省略可)
        env: 環境変数マッピング (テスト注入用)
    """
    try:
        if connection_name:
            return snowflake.connector.connect(connection_name=connection_name)
        return snowflake.connector.connect(**get_connection_params(env=env))
    except Exception as e:  # 例外を文脈付きで再ラップ
        ctx = (
            f"connections.toml connection name '{connection_name}'"
            if connection_name
            else "environment variable-based parameters"
        )
        raise RuntimeError(f"Failed to connect using {ctx}. Original error: {e}") from e


def fetch_query(
    conn: snowflake.connector.SnowflakeConnection,
    query: str,
) -> List[Dict[str, Any]]:
    """クエリを実行して結果を List[Dict] で返す副作用関数。
    カーソルの開閉は内部で管理し例外安全を確保。
    """
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    finally:
        cursor.close()


def close_connection(conn: Optional[snowflake.connector.SnowflakeConnection]) -> None:
    """接続が存在すればクローズ (冪等)。"""
    if conn:
        conn.close()


# --------------------------------------------------------------------------------------
# 最小ラッパクラス (後方互換用) - 内部は上記関数へ委譲
# --------------------------------------------------------------------------------------


class SnowflakeConnection:
    """従来インターフェイス互換の薄いラッパ。内部で関数を利用。

    .. deprecated::
        新しいコードでは関数型API（open_connection, fetch_query, close_connection）
        の直接利用を推奨します。このクラスは後方互換性のためのみ提供されています。
    """

    def __init__(self, connection_name: Optional[str] = None) -> None:
        self.connection_name = connection_name
        self.connection: Optional[snowflake.connector.SnowflakeConnection] = None

    # 内部利用 (後方互換のため残す)
    def _get_connection_params(self) -> Dict[str, Any]:  # type: ignore[override]
        return get_connection_params()

    async def connect(self) -> None:  # 非同期 API 互換
        if self.connection:
            return
        # 後方互換: テストで _get_connection_params を patch できるよう分岐を保持
        if self.connection_name:
            self.connection = open_connection(self.connection_name)
        else:
            params = self._get_connection_params()
            try:
                self.connection = snowflake.connector.connect(**params)
            except Exception as e:  # 例外メッセージを元実装に近い形で
                raise RuntimeError(
                    "Failed to connect using environment variable-based connection parameters. "
                    f"Original error: {e}"
                ) from e

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        if not self.connection:
            await self.connect()
        # mypy 的に None でないことを保証
        assert self.connection is not None
        return fetch_query(self.connection, query)

    async def close(self) -> None:
        close_connection(self.connection)
        self.connection = None


# --------------------------------------------------------------------------------------
# 関数型利用者向け公開 API (推奨)
# --------------------------------------------------------------------------------------

__all__ = [
    "get_connection_params",
    "open_connection",
    "fetch_query",
    "close_connection",
    "SnowflakeConnection",
]
