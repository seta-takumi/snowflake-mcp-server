"""Test connection management functionality."""

import os
from unittest.mock import Mock, patch, mock_open
import anyio
from snowflake_mcp_server.connection import SnowflakeConnection


class TestSnowflakeConnection:
    """Test cases for Snowflake connection management."""

    def test_connection_initialization(self) -> None:
        """Test that connection initializes with None connection."""
        connection = SnowflakeConnection()

        assert connection.connection is None

    @patch.dict(
        os.environ,
        {
            "SNOWFLAKE_ACCOUNT": "test-account",
            "SNOWFLAKE_USER": "test-user",
            "SNOWFLAKE_DATABASE": "test-db",
            "SNOWFLAKE_SCHEMA": "test-schema",
            "SNOWFLAKE_WAREHOUSE": "test-warehouse",
            "SNOWFLAKE_ROLE": "test-role",
            "SNOWFLAKE_PRIVATE_KEY_PATH": "/path/to/key.p8",
            "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE": "test-pass",
        },
    )
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake-key-data")
    @patch("snowflake_mcp_server.connection.serialization.load_pem_private_key")
    def test_get_connection_params_with_keypair(
        self, mock_load_key: Mock, mock_file: Mock
    ) -> None:
        """Test connection parameters with keypair authentication."""
        mock_private_key = Mock()
        mock_private_key.private_bytes.return_value = b"private-key-bytes"
        mock_load_key.return_value = mock_private_key

        connection = SnowflakeConnection()
        params = connection._get_connection_params()

        assert params["account"] == "test-account"
        assert params["user"] == "test-user"
        assert params["database"] == "test-db"
        assert params["schema"] == "test-schema"
        assert params["warehouse"] == "test-warehouse"
        assert params["role"] == "test-role"
        assert params["private_key"] == b"private-key-bytes"
        assert "token" not in params
        assert "authenticator" not in params

    @patch.dict(
        os.environ,
        {
            "SNOWFLAKE_ACCOUNT": "test-account",
            "SNOWFLAKE_USER": "test-user",
            "SNOWFLAKE_DATABASE": "test-db",
            "SNOWFLAKE_SCHEMA": "test-schema",
            "SNOWFLAKE_WAREHOUSE": "test-warehouse",
            "SNOWFLAKE_ROLE": "test-role",
            "SNOWFLAKE_OAUTH_TOKEN": "test-oauth-token",
        },
    )
    def test_get_connection_params_with_oauth(self) -> None:
        """Test connection parameters with OAuth authentication."""
        connection = SnowflakeConnection()
        params = connection._get_connection_params()

        assert params["account"] == "test-account"
        assert params["user"] == "test-user"
        assert params["database"] == "test-db"
        assert params["schema"] == "test-schema"
        assert params["warehouse"] == "test-warehouse"
        assert params["role"] == "test-role"
        assert params["token"] == "test-oauth-token"
        assert params["authenticator"] == "oauth"
        assert "private_key" not in params

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

    @patch("builtins.open", new_callable=mock_open, read_data=b"fake-key-data")
    @patch("snowflake_mcp_server.connection.serialization.load_pem_private_key")
    def test_private_key_loading_without_passphrase(
        self, mock_load_key: Mock, mock_file: Mock
    ) -> None:
        """Test private key loading without passphrase."""
        mock_private_key = Mock()
        mock_private_key.private_bytes.return_value = b"private-key-bytes"
        mock_load_key.return_value = mock_private_key

        with patch.dict(
            os.environ,
            {
                "SNOWFLAKE_ACCOUNT": "test-account",
                "SNOWFLAKE_USER": "test-user",
                "SNOWFLAKE_DATABASE": "test-db",
                "SNOWFLAKE_SCHEMA": "test-schema",
                "SNOWFLAKE_WAREHOUSE": "test-warehouse",
                "SNOWFLAKE_ROLE": "test-role",
                "SNOWFLAKE_PRIVATE_KEY_PATH": "/path/to/key.p8",
            },
        ):
            connection = SnowflakeConnection()
            params = connection._get_connection_params()

            mock_load_key.assert_called_once_with(b"fake-key-data", password=None)
            assert params["private_key"] == b"private-key-bytes"

    @patch("builtins.open", new_callable=mock_open, read_data=b"fake-key-data")
    @patch("snowflake_mcp_server.connection.serialization.load_pem_private_key")
    def test_private_key_loading_with_passphrase(
        self, mock_load_key: Mock, mock_file: Mock
    ) -> None:
        """Test private key loading with passphrase."""
        mock_private_key = Mock()
        mock_private_key.private_bytes.return_value = b"private-key-bytes"
        mock_load_key.return_value = mock_private_key

        with patch.dict(
            os.environ,
            {
                "SNOWFLAKE_ACCOUNT": "test-account",
                "SNOWFLAKE_USER": "test-user",
                "SNOWFLAKE_DATABASE": "test-db",
                "SNOWFLAKE_SCHEMA": "test-schema",
                "SNOWFLAKE_WAREHOUSE": "test-warehouse",
                "SNOWFLAKE_ROLE": "test-role",
                "SNOWFLAKE_PRIVATE_KEY_PATH": "/path/to/key.p8",
                "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE": "test-pass",
            },
        ):
            connection = SnowflakeConnection()
            params = connection._get_connection_params()

            mock_load_key.assert_called_once_with(
                b"fake-key-data", password=b"test-pass"
            )
            assert params["private_key"] == b"private-key-bytes"
