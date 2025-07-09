"""Test MCP server functionality."""

from unittest.mock import patch
import anyio
from snowflake_mcp.server import SnowflakeMCPServer


class TestSnowflakeMCPServer:
    """Test cases for Snowflake MCP Server."""

    def test_server_initialization(self) -> None:
        """Test that server initializes correctly."""
        server = SnowflakeMCPServer()

        assert server.connection is not None
        assert server.server is not None
        assert server.query_validator is not None

    def test_is_read_only_query_delegates_to_validator(self) -> None:
        """Test that read-only check delegates to query validator."""
        server = SnowflakeMCPServer()

        with patch.object(
            server.query_validator, "is_read_only", return_value=True
        ) as mock_validator:
            result = server._is_read_only_query("SELECT 1")

            mock_validator.assert_called_once_with("SELECT 1")
            assert result is True

    def test_query_tool_rejects_write_queries(self) -> None:
        """Test that query tool rejects write queries."""
        server = SnowflakeMCPServer()

        with patch.object(server, "_is_read_only_query", return_value=False):

            async def run_test():
                try:
                    await server._query_tool("INSERT INTO test VALUES (1)")
                    assert False, "Expected ValueError"
                except ValueError as e:
                    assert "Only read-only queries are allowed" in str(e)
                    return True

            result = anyio.run(run_test)
            assert result is True

    def test_query_tool_executes_read_only_queries(self) -> None:
        """Test that query tool executes read-only queries successfully."""
        server = SnowflakeMCPServer()
        mock_results = [{"column1": "value1"}]

        with (
            patch.object(server, "_is_read_only_query", return_value=True),
            patch.object(server.connection, "execute_query", return_value=mock_results),
        ):

            async def run_test():
                result = await server._query_tool("SELECT 1")
                return result

            result = anyio.run(run_test)

            assert result == mock_results

    def test_query_tool_handles_execution_errors(self) -> None:
        """Test that query tool handles execution errors gracefully."""
        server = SnowflakeMCPServer()

        with (
            patch.object(server, "_is_read_only_query", return_value=True),
            patch.object(
                server.connection,
                "execute_query",
                side_effect=Exception("Connection error"),
            ),
        ):

            async def run_test():
                try:
                    await server._query_tool("SELECT 1")
                    assert False, "Expected RuntimeError"
                except RuntimeError as e:
                    assert "Query execution failed: Connection error" in str(e)
                    return True

            result = anyio.run(run_test)
            assert result is True

    def test_list_tables_tool_executes_show_tables(self) -> None:
        """Test that list_tables tool executes SHOW TABLES query."""
        server = SnowflakeMCPServer()
        mock_results = [{"name": "table1"}, {"name": "table2"}]

        with patch.object(
            server.connection, "execute_query", return_value=mock_results
        ) as mock_execute:

            async def run_test():
                result = await server._list_tables_tool()
                return result

            result = anyio.run(run_test)

            mock_execute.assert_called_once_with("SHOW TABLES")
            assert result == mock_results

    def test_list_tables_tool_handles_errors(self) -> None:
        """Test that list_tables tool handles errors gracefully."""
        server = SnowflakeMCPServer()

        with patch.object(
            server.connection, "execute_query", side_effect=Exception("Access denied")
        ):

            async def run_test():
                try:
                    await server._list_tables_tool()
                    assert False, "Expected RuntimeError"
                except RuntimeError as e:
                    assert "Failed to list tables: Access denied" in str(e)
                    return True

            result = anyio.run(run_test)
            assert result is True

    def test_describe_table_tool_executes_describe_query(self) -> None:
        """Test that describe_table tool executes DESCRIBE query."""
        server = SnowflakeMCPServer()
        mock_results = [{"name": "id", "type": "NUMBER"}]

        with patch.object(
            server.connection, "execute_query", return_value=mock_results
        ) as mock_execute:

            async def run_test():
                result = await server._describe_table_tool("users")
                return result

            result = anyio.run(run_test)

            mock_execute.assert_called_once_with("DESCRIBE TABLE users")
            assert result == mock_results

    def test_describe_table_tool_handles_errors(self) -> None:
        """Test that describe_table tool handles errors gracefully."""
        server = SnowflakeMCPServer()

        with patch.object(
            server.connection, "execute_query", side_effect=Exception("Table not found")
        ):

            async def run_test():
                try:
                    await server._describe_table_tool("nonexistent")
                    assert False, "Expected RuntimeError"
                except RuntimeError as e:
                    assert "Failed to describe table: Table not found" in str(e)
                    return True

            result = anyio.run(run_test)
            assert result is True

    def test_get_schema_tool_executes_describe_schema(self) -> None:
        """Test that get_schema tool executes DESCRIBE SCHEMA query."""
        server = SnowflakeMCPServer()
        mock_results = [{"name": "PUBLIC", "kind": "SCHEMA"}]

        with patch.object(
            server.connection, "execute_query", return_value=mock_results
        ) as mock_execute:

            async def run_test():
                result = await server._get_schema_tool()
                return result

            result = anyio.run(run_test)

            mock_execute.assert_called_once_with("DESCRIBE SCHEMA")
            assert result == mock_results

    def test_get_schema_tool_handles_errors(self) -> None:
        """Test that get_schema tool handles errors gracefully."""
        server = SnowflakeMCPServer()

        with patch.object(
            server.connection,
            "execute_query",
            side_effect=Exception("Schema access denied"),
        ):

            async def run_test():
                try:
                    await server._get_schema_tool()
                    assert False, "Expected RuntimeError"
                except RuntimeError as e:
                    assert "Failed to get schema: Schema access denied" in str(e)
                    return True

            result = anyio.run(run_test)
            assert result is True
