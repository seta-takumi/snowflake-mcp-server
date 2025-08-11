"""MCP サーバ (関数型スタイル寄り) 構成モジュール。

従来の create_snowflake_mcp_server API を維持しつつ、
ツール登録ロジックを関数ベースに分離してテスタビリティと拡張性を向上。"""

from __future__ import annotations

from typing import Awaitable, Callable, Dict, List, Any

from mcp.server.fastmcp import FastMCP
from snowflake_mcp_server.connection import (
    open_connection,
    fetch_query,
    close_connection,
)
from snowflake_mcp_server.query_validator import is_read_only_query
import snowflake.connector

# 型エイリアス
AsyncTool = Callable[..., Awaitable[List[Dict[str, Any]]]]
ConnectionFactory = Callable[[], snowflake.connector.SnowflakeConnection]


async def _execute_with_connection(
    connection_factory: ConnectionFactory, query: str
) -> List[Dict[str, Any]]:
    """接続を開いてクエリを実行し、確実にクローズする。"""
    conn = connection_factory()
    try:
        return fetch_query(conn, query)
    finally:
        close_connection(conn)


def _wrap_errors(
    message: str, coro_factory: Callable[[], Awaitable[List[Dict[str, Any]]]]
) -> AsyncTool:
    """共通エラーハンドリングラッパ (関数型合成用)。"""

    async def _inner() -> List[Dict[str, Any]]:
        try:
            return await coro_factory()
        except Exception as e:  # メッセージを統一して再ラップ
            raise RuntimeError(f"{message}: {e}") from e

    return _inner  # type: ignore[return-value]


def register_tools(
    mcp: FastMCP,
    *,
    connection_factory: ConnectionFactory,
    is_read_only: Callable[[str], bool],
) -> None:
    """ツールを FastMCP インスタンスへ登録 (副作用のみ)。

    引数を全て注入することでテスト時に任意のモックへ差し替え可能。
    """

    @mcp.tool()
    async def query(sql: str) -> List[Dict[str, Any]]:  # noqa: D401 (簡潔で良い)
        if not is_read_only(sql):
            raise ValueError("Only read-only queries are allowed")
        return await _wrap_errors(
            "Query execution failed",
            lambda: _execute_with_connection(connection_factory, sql),
        )()

    @mcp.tool()
    async def list_tables() -> List[Dict[str, Any]]:
        return await _wrap_errors(
            "Failed to list tables",
            lambda: _execute_with_connection(connection_factory, "SHOW TABLES"),
        )()

    @mcp.tool()
    async def describe_table(table_name: str) -> List[Dict[str, Any]]:
        return await _wrap_errors(
            "Failed to describe table",
            lambda: _execute_with_connection(
                connection_factory, f"DESCRIBE TABLE {table_name}"
            ),
        )()

    @mcp.tool()
    async def get_schema() -> List[Dict[str, Any]]:
        return await _wrap_errors(
            "Failed to get schema",
            lambda: _execute_with_connection(connection_factory, "DESCRIBE SCHEMA"),
        )()


def create_snowflake_mcp_server(connection_name: str | None = None) -> FastMCP:
    """Snowflake MCP サーバを生成 (関数型スタイル)。"""

    def connection_factory() -> snowflake.connector.SnowflakeConnection:
        return open_connection(connection_name=connection_name)

    mcp = FastMCP("snowflake-mcp")
    register_tools(
        mcp, connection_factory=connection_factory, is_read_only=is_read_only_query
    )
    return mcp


__all__ = [
    "create_snowflake_mcp_server",
    "register_tools",
]
