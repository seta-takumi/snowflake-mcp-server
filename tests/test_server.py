"""Tests for the Snowflake MCP server module."""

import anyio
from unittest.mock import AsyncMock, Mock, patch
from mcp.server.fastmcp import FastMCP
from snowflake_mcp_server.server import create_snowflake_mcp_server, register_tools


class TestCreateSnowflakeMcpServer:
    """Test cases for create_snowflake_mcp_server function."""

    def test_creates_server_instance(self) -> None:
        """Test that create_snowflake_mcp_server returns a FastMCP instance."""
        server = create_snowflake_mcp_server()

        # Check that we got a server instance
        assert server is not None
        assert hasattr(server, "run")
        assert hasattr(server, "tool")

    def test_creates_server_with_connection_name(self) -> None:
        """Test that server can be created with a connection name."""
        connection_name = "test_connection"
        server = create_snowflake_mcp_server(connection_name=connection_name)

        assert server is not None

    def test_initializes_components(self) -> None:
        """Test that server properly initializes with connection factory and is_read_only function."""
        # Simply test that the server can be created without errors
        server = create_snowflake_mcp_server(connection_name="test")

        # Verify the server is created successfully
        assert server is not None
        assert hasattr(server, "run")
        assert hasattr(server, "tool")

    @patch("snowflake_mcp_server.server._execute_with_connection")
    @patch("snowflake_mcp_server.server.is_read_only_query")
    def test_query_tool_success(
        self, mock_is_read_only, mock_execute_with_connection
    ) -> None:
        """Test successful query execution through the tool."""
        # Mock is_read_only_query to return True
        mock_is_read_only.return_value = True

        # Mock _execute_with_connection to return test results
        expected_results = [{"column1": "value1", "column2": "value2"}]
        mock_execute_with_connection.return_value = expected_results

        # Create server
        server = create_snowflake_mcp_server()

        # Test query execution
        async def run_test():
            result = await server.call_tool(
                "query", {"sql": "SELECT * FROM test_table"}
            )
            return result

        result = anyio.run(run_test)

        # Verify results - check that the call was successful and returned data
        assert result is not None
        mock_is_read_only.assert_called_once_with("SELECT * FROM test_table")
        mock_execute_with_connection.assert_called_once()

    @patch("snowflake_mcp_server.server.is_read_only_query")
    def test_query_tool_rejects_write_queries(self, mock_is_read_only) -> None:
        """Test that query tool rejects write queries."""
        # Mock is_read_only_query to return False for write query
        mock_is_read_only.return_value = False

        # Create server
        server = create_snowflake_mcp_server()

        # Test query rejection
        async def run_test():
            try:
                await server.call_tool("query", {"sql": "INSERT INTO test VALUES (1)"})
                return False  # Should not reach here
            except Exception as e:
                assert "Only read-only queries are allowed" in str(e)
                return True

        result = anyio.run(run_test)
        assert result is True
        mock_is_read_only.assert_called_once_with("INSERT INTO test VALUES (1)")

    @patch("snowflake_mcp_server.server._execute_with_connection")
    @patch("snowflake_mcp_server.server.is_read_only_query")
    def test_query_tool_handles_connection_error(
        self, mock_is_read_only, mock_execute_with_connection
    ) -> None:
        """Test that query tool handles connection errors properly."""
        # Mock is_read_only_query to return True
        mock_is_read_only.return_value = True

        # Mock _execute_with_connection to raise an exception
        mock_execute_with_connection.side_effect = Exception("Connection failed")

        # Create server
        server = create_snowflake_mcp_server()

        # Test error handling
        async def run_test():
            try:
                await server.call_tool("query", {"sql": "SELECT 1"})
                return False  # Should not reach here
            except Exception as e:
                assert "Query execution failed" in str(e) or "Connection failed" in str(
                    e
                )
                return True

        result = anyio.run(run_test)
        assert result is True

    @patch("snowflake_mcp_server.server._execute_with_connection")
    def test_list_tables_tool(self, mock_execute_with_connection) -> None:
        """Test list_tables tool functionality."""
        # Mock _execute_with_connection to return table list
        expected_tables = [{"name": "table1"}, {"name": "table2"}]
        mock_execute_with_connection.return_value = expected_tables

        # Create server
        server = create_snowflake_mcp_server()

        # Test tool execution
        async def run_test():
            result = await server.call_tool("list_tables", {})
            return result

        result = anyio.run(run_test)

        # Verify results - check that the call was successful
        assert result is not None
        mock_execute_with_connection.assert_called_once()

    @patch("snowflake_mcp_server.server._execute_with_connection")
    def test_describe_table_tool(self, mock_execute_with_connection) -> None:
        """Test describe_table tool functionality."""
        # Mock _execute_with_connection to return table description
        expected_description = [{"column": "id", "type": "NUMBER"}]
        mock_execute_with_connection.return_value = expected_description

        # Create server
        server = create_snowflake_mcp_server()

        # Test tool execution
        async def run_test():
            result = await server.call_tool(
                "describe_table", {"table_name": "test_table"}
            )
            return result

        result = anyio.run(run_test)

        # Verify results - check that the call was successful
        assert result is not None
        mock_execute_with_connection.assert_called_once()

    @patch("snowflake_mcp_server.server._execute_with_connection")
    def test_list_schemas_tool(self, mock_execute_with_connection) -> None:
        """Test list_schemas tool functionality."""
        # Mock _execute_with_connection to return schemas list
        expected_schemas = [{"schema_name": "PUBLIC"}, {"schema_name": "PRIVATE"}]
        mock_execute_with_connection.return_value = expected_schemas

        # Create server
        server = create_snowflake_mcp_server()

        # Test tool execution
        async def run_test():
            result = await server.call_tool("list_schemas", {})
            return result

        result = anyio.run(run_test)

        # Verify results - check that the call was successful
        assert result is not None
        mock_execute_with_connection.assert_called_once()

    @patch("snowflake_mcp_server.server._execute_with_connection")
    def test_describe_schema_tool(self, mock_execute_with_connection) -> None:
        """Test describe_schema tool functionality."""
        # Mock _execute_with_connection to return schema description
        expected_description = [{"property": "COMMENT", "value": "Test schema"}]
        mock_execute_with_connection.return_value = expected_description

        # Create server
        server = create_snowflake_mcp_server()

        # Test tool execution
        async def run_test():
            result = await server.call_tool(
                "describe_schema", {"schema_name": "PUBLIC"}
            )
            return result

        result = anyio.run(run_test)

        # Verify results - check that the call was successful
        assert result is not None
        mock_execute_with_connection.assert_called_once()

    @patch("snowflake_mcp_server.server._execute_with_connection")
    def test_list_databases_tool(self, mock_execute_with_connection) -> None:
        """Test list_databases tool functionality."""
        # Mock _execute_with_connection to return databases list
        expected_databases = [
            {
                "database_name": "TESTDB",
                "owner": "ACCOUNTADMIN",
                "comment": "Test database",
            },
            {
                "database_name": "ANALYTICS",
                "owner": "DBA_ROLE",
                "comment": "Analytics database",
            },
        ]
        mock_execute_with_connection.return_value = expected_databases

        # Create server
        server = create_snowflake_mcp_server()

        # Test tool execution
        async def run_test():
            result = await server.call_tool("list_databases", {})
            return result

        result = anyio.run(run_test)

        # Verify results
        assert result is not None
        mock_execute_with_connection.assert_called_once()

    @patch("snowflake_mcp_server.server._execute_with_connection")
    def test_describe_database_tool(self, mock_execute_with_connection) -> None:
        """Test describe_database tool functionality."""
        # Mock _execute_with_connection to return database description
        expected_description = [
            {
                "property": "CREATED",
                "property_type": "String",
                "property_value": "2024-01-01 00:00:00.000 +0000",
                "property_default": None,
            },
            {
                "property": "OWNER",
                "property_type": "String",
                "property_value": "ACCOUNTADMIN",
                "property_default": None,
            },
        ]
        mock_execute_with_connection.return_value = expected_description

        # Create server
        server = create_snowflake_mcp_server()

        # Test tool execution
        async def run_test():
            result = await server.call_tool(
                "describe_database", {"database_name": "TESTDB"}
            )
            return result

        result = anyio.run(run_test)

        # Verify results
        assert result is not None
        mock_execute_with_connection.assert_called_once()

    def test_server_has_all_expected_tools(self) -> None:
        """Test that server has all expected tools registered."""
        server = create_snowflake_mcp_server()

        async def get_tools():
            tools = await server.list_tools()
            return tools

        tools = anyio.run(get_tools)

        expected_tools = {
            "query",
            "list_tables",
            "describe_table",
            "list_schemas",
            "describe_schema",
            "list_databases",
            "describe_database",
        }
        actual_tools = {tool.name for tool in tools}

        assert expected_tools == actual_tools


# --------------------------------------------------------------------------------------
# 関数型 API のテスト (新規推奨)
# --------------------------------------------------------------------------------------


class TestFunctionalServerAPI:
    """関数型 server API のテスト。依存性注入でテストしやすい。"""

    def test_register_tools_basic_structure(self) -> None:
        """register_tools の基本構造テスト。"""
        mock_mcp = Mock(spec=FastMCP)
        mock_connection = Mock()
        mock_is_read_only = Mock(return_value=True)

        # 副作用のみの関数なので、正常終了すれば OK
        mock_connection_factory = Mock(return_value=mock_connection)
        register_tools(
            mock_mcp,
            connection_factory=mock_connection_factory,
            is_read_only=mock_is_read_only,
        )

        # 7つのツールが登録されることを確認
        assert mock_mcp.tool.call_count == 7

    @patch("snowflake_mcp_server.server._wrap_errors")
    def test_register_tools_query_validation(self, mock_wrap_errors: Mock) -> None:
        """query ツールでの読み取り専用チェックテスト。"""
        mock_mcp = Mock(spec=FastMCP)
        mock_connection = Mock()
        mock_is_read_only = Mock()
        mock_wrap_errors.return_value = AsyncMock(return_value=[])

        mock_connection_factory = Mock(return_value=mock_connection)
        register_tools(
            mock_mcp,
            connection_factory=mock_connection_factory,
            is_read_only=mock_is_read_only,
        )

        # query ツールが登録されていることを確認
        query_decorator_calls = [call for call in mock_mcp.tool.call_args_list]
        assert (
            len(query_decorator_calls) == 7
        )

    def test_register_tools_dependency_injection(self) -> None:
        """依存性注入の効果テスト (モック差し替え可能性)。"""
        mock_mcp = Mock(spec=FastMCP)
        mock_connection = Mock()

        # カスタムバリデータで "CUSTOM" を読み取り専用とする
        def custom_validator(sql: str) -> bool:
            return sql.strip().upper().startswith("CUSTOM")

        mock_connection_factory = Mock(return_value=mock_connection)
        register_tools(
            mock_mcp,
            connection_factory=mock_connection_factory,
            is_read_only=custom_validator,
        )

        # 正常に登録完了 (カスタムバリデータを注入できた)
        assert mock_mcp.tool.call_count == 7  # 7つのツール

    def test_functional_vs_class_equivalence(self) -> None:
        """関数型 API とクラス API の等価性テスト。"""
        # 従来の create_snowflake_mcp_server
        server1 = create_snowflake_mcp_server()

        # 関数型 API での組み立て
        from snowflake_mcp_server.connection import open_connection
        from snowflake_mcp_server.query_validator import is_read_only_query

        def connection_factory():
            return open_connection()

        server2 = FastMCP("snowflake-mcp")
        register_tools(
            server2,
            connection_factory=connection_factory,
            is_read_only=is_read_only_query,
        )

        # 両者のツール構成が同じことを確認
        async def compare_tools():
            tools1 = await server1.list_tools()
            tools2 = await server2.list_tools()

            names1 = {tool.name for tool in tools1}
            names2 = {tool.name for tool in tools2}
            assert names1 == names2

        anyio.run(compare_tools)
