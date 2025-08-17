"""Test connection management functionality."""

from unittest.mock import Mock, patch, mock_open
import anyio
import pytest
from snowflake_mcp_server.connection import (
    SnowflakeConnection,
    get_connection_params,
    open_connection,
    fetch_query,
    close_connection,
)


class TestSnowflakeConnection:
    """Test cases for Snowflake connection management."""

    def test_connection_initialization(self) -> None:
        """Test that connection initializes with None connection."""
        connection = SnowflakeConnection()

        assert connection.connection is None

    @patch("snowflake_mcp_server.connection.snowflake.connector.connect")
    @patch.object(SnowflakeConnection, "_get_connection_params")
    def test_connect_creates_connection(
        self, mock_get_params: Mock, mock_connect: Mock
    ) -> None:
        """Test that connect method creates a connection."""
        mock_get_params.return_value = {"account": "test-account"}
        mock_snowflake_conn = Mock()
        mock_connect.return_value = mock_snowflake_conn

        connection = SnowflakeConnection()

        async def run_test():
            await connection.connect()

        anyio.run(run_test)

        assert connection.connection == mock_snowflake_conn
        mock_connect.assert_called_once_with(account="test-account")

    @patch("snowflake_mcp_server.connection.snowflake.connector.connect")
    @patch.object(SnowflakeConnection, "_get_connection_params")
    def test_execute_query_connects_if_not_connected(
        self, mock_get_params: Mock, mock_connect: Mock
    ) -> None:
        """Test that execute_query connects if not already connected."""
        mock_get_params.return_value = {"account": "test-account"}
        mock_snowflake_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.description = [["column1"], ["column2"]]
        mock_cursor.fetchall.return_value = [("value1", "value2")]
        mock_snowflake_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_snowflake_conn

        connection = SnowflakeConnection()

        async def run_test():
            return await connection.execute_query("SELECT 1")

        result = anyio.run(run_test)

        assert connection.connection == mock_snowflake_conn
        mock_connect.assert_called_once_with(account="test-account")
        mock_cursor.execute.assert_called_once_with("SELECT 1")
        assert result == [{"column1": "value1", "column2": "value2"}]

    def test_execute_query_uses_existing_connection(self) -> None:
        """Test that execute_query uses existing connection if available."""
        mock_snowflake_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.description = [["column1"]]
        mock_cursor.fetchall.return_value = [("value1",)]
        mock_snowflake_conn.cursor.return_value = mock_cursor

        connection = SnowflakeConnection()
        connection.connection = mock_snowflake_conn

        async def run_test():
            return await connection.execute_query("SELECT 1")

        result = anyio.run(run_test)

        mock_cursor.execute.assert_called_once_with("SELECT 1")
        assert result == [{"column1": "value1"}]

    def test_execute_query_closes_cursor(self) -> None:
        """Test that execute_query closes the cursor after use."""
        mock_snowflake_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.description = [["column1"]]
        mock_cursor.fetchall.return_value = [("value1",)]
        mock_snowflake_conn.cursor.return_value = mock_cursor

        connection = SnowflakeConnection()
        connection.connection = mock_snowflake_conn

        async def run_test():
            await connection.execute_query("SELECT 1")

        anyio.run(run_test)

        mock_cursor.close.assert_called_once()

    def test_close_connection_when_exists(self) -> None:
        """Test that close method closes existing connection."""
        mock_snowflake_conn = Mock()
        connection = SnowflakeConnection()
        connection.connection = mock_snowflake_conn

        async def run_test():
            await connection.close()

        anyio.run(run_test)

        mock_snowflake_conn.close.assert_called_once()
        assert connection.connection is None

    def test_close_connection_when_none(self) -> None:
        """Test that close method handles None connection gracefully."""
        connection = SnowflakeConnection()

        async def run_test():
            await connection.close()

        anyio.run(run_test)

        assert connection.connection is None

    # _get_connection_params / private key 読み込みパスの詳細テストは
    # 関数型 API テストへ移行したためここでは削除。


# --------------------------------------------------------------------------------------
# 関数型スタイルのテスト (新規推奨)
# --------------------------------------------------------------------------------------


class TestFunctionalConnectionAPI:
    """関数型 API のテスト。純関数は副作用がないためテストが簡潔。"""

    def test_get_connection_params_basic(self) -> None:
        """環境変数からの基本パラメータ構築テスト。"""
        env = {
            "SNOWFLAKE_ACCOUNT": "test-account",
            "SNOWFLAKE_USER": "test-user",
            "SNOWFLAKE_DATABASE": "test-db",
        }
        params = get_connection_params(env)

        assert params["account"] == "test-account"
        assert params["user"] == "test-user"
        assert params["database"] == "test-db"
        assert "schema" not in params  # スキーマは任意なので含まれない
        assert "private_key" not in params
        assert "token" not in params

    def test_get_connection_params_with_schema(self) -> None:
        """スキーマが指定された場合のテスト。"""
        env = {
            "SNOWFLAKE_ACCOUNT": "test-account",
            "SNOWFLAKE_USER": "test-user",
            "SNOWFLAKE_DATABASE": "test-db",
            "SNOWFLAKE_SCHEMA": "test-schema",
        }
        params = get_connection_params(env)

        assert params["account"] == "test-account"
        assert params["user"] == "test-user"
        assert params["database"] == "test-db"
        assert params["schema"] == "test-schema"

    def test_get_connection_params_without_schema(self) -> None:
        """スキーマが指定されていない場合のテスト。"""
        env = {
            "SNOWFLAKE_ACCOUNT": "test-account",
            "SNOWFLAKE_USER": "test-user",
            "SNOWFLAKE_DATABASE": "test-db",
            "SNOWFLAKE_WAREHOUSE": "test-warehouse",
        }
        params = get_connection_params(env)

        assert params["account"] == "test-account"
        assert params["user"] == "test-user"
        assert params["database"] == "test-db"
        assert params["warehouse"] == "test-warehouse"
        assert "schema" not in params  # スキーマは任意なので含まれない

    def test_get_connection_params_oauth(self) -> None:
        """OAuth トークン設定のテスト。"""
        env = {
            "SNOWFLAKE_ACCOUNT": "test-account",
            "SNOWFLAKE_USER": "test-user",
            "SNOWFLAKE_OAUTH_TOKEN": "oauth-token-123",
        }
        params = get_connection_params(env)

        assert params["token"] == "oauth-token-123"
        assert params["authenticator"] == "oauth"

    @patch("builtins.open", new_callable=mock_open, read_data=b"fake-pem-data")
    @patch("snowflake_mcp_server.connection.serialization.load_pem_private_key")
    def test_get_connection_params_keypair(
        self, mock_load_key: Mock, mock_file: Mock
    ) -> None:
        """KeyPair 認証設定のテスト (ファイル読み込み副作用あり)。"""
        mock_private_key = Mock()
        mock_private_key.private_bytes.return_value = b"serialized-key"
        mock_load_key.return_value = mock_private_key

        env = {
            "SNOWFLAKE_ACCOUNT": "test-account",
            "SNOWFLAKE_PRIVATE_KEY_PATH": "/test/key.p8",
            "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE": "secret",
        }
        params = get_connection_params(env)

        assert params["private_key"] == b"serialized-key"
        mock_load_key.assert_called_once_with(b"fake-pem-data", password=b"secret")

    @patch("builtins.open", new_callable=mock_open, read_data=b"fake-pem-data")
    @patch("snowflake_mcp_server.connection.serialization.load_pem_private_key")
    def test_get_connection_params_keypair_without_passphrase(
        self, mock_load_key: Mock, mock_file: Mock
    ) -> None:
        """KeyPair 認証 (パスフレーズ無し) のテスト。"""
        mock_private_key = Mock()
        mock_private_key.private_bytes.return_value = b"serialized-key"
        mock_load_key.return_value = mock_private_key

        env = {
            "SNOWFLAKE_ACCOUNT": "test-account",
            "SNOWFLAKE_PRIVATE_KEY_PATH": "/test/key.p8",
        }
        params = get_connection_params(env)

        assert params["private_key"] == b"serialized-key"
        mock_load_key.assert_called_once_with(b"fake-pem-data", password=None)

    @patch("snowflake_mcp_server.connection.snowflake.connector.connect")
    def test_open_connection_with_name(self, mock_connect: Mock) -> None:
        """connections.toml 経由の接続テスト。"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        result = open_connection("test-connection")

        assert result == mock_conn
        mock_connect.assert_called_once_with(connection_name="test-connection")

    @patch("snowflake_mcp_server.connection.snowflake.connector.connect")
    def test_open_connection_with_env(self, mock_connect: Mock) -> None:
        """環境変数経由の接続テスト。"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        env = {"SNOWFLAKE_ACCOUNT": "test-account", "SNOWFLAKE_USER": "test-user"}
        result = open_connection(env=env)

        assert result == mock_conn
        # get_connection_params(env) の結果で connect が呼ばれることを確認
        mock_connect.assert_called_once()
        call_args = mock_connect.call_args[1]  # kwargs
        assert call_args["account"] == "test-account"
        assert call_args["user"] == "test-user"

    def test_fetch_query_success(self) -> None:
        """クエリ実行成功ケースのテスト。"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.description = [["col1"], ["col2"]]
        mock_cursor.fetchall.return_value = [("val1", "val2"), ("val3", "val4")]
        mock_conn.cursor.return_value = mock_cursor

        result = fetch_query(mock_conn, "SELECT * FROM test")

        expected = [
            {"col1": "val1", "col2": "val2"},
            {"col1": "val3", "col2": "val4"},
        ]
        assert result == expected
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test")
        mock_cursor.close.assert_called_once()

    def test_fetch_query_cursor_cleanup_on_exception(self) -> None:
        """例外発生時でもカーソルがクローズされることを確認。"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("DB Error")
        mock_conn.cursor.return_value = mock_cursor

        with pytest.raises(Exception, match="DB Error"):
            fetch_query(mock_conn, "INVALID SQL")

        mock_cursor.close.assert_called_once()  # 例外時も cleanup

    def test_close_connection_with_valid_conn(self) -> None:
        """有効な接続のクローズテスト。"""
        mock_conn = Mock()
        close_connection(mock_conn)
        mock_conn.close.assert_called_once()

    def test_close_connection_with_none(self) -> None:
        """None 接続のクローズテスト (冪等性)。"""
        close_connection(None)  # 例外が発生しないことを確認
