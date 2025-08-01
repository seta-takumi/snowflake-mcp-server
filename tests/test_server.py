"""Tests for the Snowflake MCP server module."""

import pytest
import anyio
from unittest.mock import AsyncMock, Mock, patch
from snowflake_mcp_server.server import create_snowflake_mcp_server


class TestCreateSnowflakeMcpServer:
    """Test cases for create_snowflake_mcp_server function."""

    def test_creates_server_instance(self) -> None:
        """Test that create_snowflake_mcp_server returns a FastMCP instance."""
        server = create_snowflake_mcp_server()
        
        # Check that we got a server instance
        assert server is not None
        assert hasattr(server, 'run')
        assert hasattr(server, 'tool')

    def test_creates_server_with_connection_name(self) -> None:
        """Test that server can be created with a connection name."""
        connection_name = "test_connection"
        server = create_snowflake_mcp_server(connection_name=connection_name)
        
        assert server is not None

    @patch('snowflake_mcp_server.server.SnowflakeConnection')
    @patch('snowflake_mcp_server.server.QueryValidator')
    def test_initializes_components(self, mock_validator_class, mock_connection_class) -> None:
        """Test that server properly initializes connection and validator."""
        mock_connection = Mock()
        mock_validator = Mock()
        mock_connection_class.return_value = mock_connection
        mock_validator_class.return_value = mock_validator
        
        server = create_snowflake_mcp_server(connection_name="test")
        
        # Verify components were initialized
        mock_connection_class.assert_called_once_with(connection_name="test")
        mock_validator_class.assert_called_once()

    @patch('snowflake_mcp_server.server.SnowflakeConnection')
    @patch('snowflake_mcp_server.server.QueryValidator')
    def test_query_tool_success(self, mock_validator_class, mock_connection_class) -> None:
        """Test successful query execution through the tool."""
        # Setup mocks
        mock_connection = AsyncMock()
        mock_validator = Mock()
        mock_connection_class.return_value = mock_connection
        mock_validator_class.return_value = mock_validator
        
        # Mock validator to return True for read-only
        mock_validator.is_read_only.return_value = True
        
        # Mock connection to return test results
        expected_results = [{"column1": "value1", "column2": "value2"}]
        mock_connection.execute_query.return_value = expected_results
        
        # Create server
        server = create_snowflake_mcp_server()
        
        # Test query execution
        async def run_test():
            result = await server.call_tool("query", {"sql": "SELECT * FROM test_table"})
            return result
            
        result = anyio.run(run_test)
        
        # Verify results - check that the call was successful and returned data
        assert result is not None
        mock_validator.is_read_only.assert_called_once_with("SELECT * FROM test_table")
        mock_connection.execute_query.assert_called_once_with("SELECT * FROM test_table")

    @patch('snowflake_mcp_server.server.SnowflakeConnection')
    @patch('snowflake_mcp_server.server.QueryValidator')
    def test_query_tool_rejects_write_queries(self, mock_validator_class, mock_connection_class) -> None:
        """Test that query tool rejects write queries."""
        # Setup mocks
        mock_connection = AsyncMock()
        mock_validator = Mock()
        mock_connection_class.return_value = mock_connection
        mock_validator_class.return_value = mock_validator
        
        # Mock validator to return False for write query
        mock_validator.is_read_only.return_value = False
        
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
        mock_validator.is_read_only.assert_called_once_with("INSERT INTO test VALUES (1)")
        mock_connection.execute_query.assert_not_called()

    @patch('snowflake_mcp_server.server.SnowflakeConnection')
    @patch('snowflake_mcp_server.server.QueryValidator')
    def test_query_tool_handles_connection_error(self, mock_validator_class, mock_connection_class) -> None:
        """Test that query tool handles connection errors properly."""
        # Setup mocks
        mock_connection = AsyncMock()
        mock_validator = Mock()
        mock_connection_class.return_value = mock_connection
        mock_validator_class.return_value = mock_validator
        
        # Mock validator to return True
        mock_validator.is_read_only.return_value = True
        
        # Mock connection to raise an exception
        mock_connection.execute_query.side_effect = Exception("Connection failed")
        
        # Create server
        server = create_snowflake_mcp_server()
        
        # Test error handling
        async def run_test():
            try:
                await server.call_tool("query", {"sql": "SELECT 1"})
                return False  # Should not reach here
            except Exception as e:
                assert "Connection failed" in str(e)
                return True
                
        result = anyio.run(run_test)
        assert result is True

    @patch('snowflake_mcp_server.server.SnowflakeConnection')
    @patch('snowflake_mcp_server.server.QueryValidator')
    def test_list_tables_tool(self, mock_validator_class, mock_connection_class) -> None:
        """Test list_tables tool functionality."""
        # Setup mocks
        mock_connection = AsyncMock()
        mock_validator = Mock()
        mock_connection_class.return_value = mock_connection
        mock_validator_class.return_value = mock_validator
        
        # Mock connection to return table list
        expected_tables = [{"name": "table1"}, {"name": "table2"}]
        mock_connection.execute_query.return_value = expected_tables
        
        # Create server
        server = create_snowflake_mcp_server()
        
        # Test tool execution
        async def run_test():
            result = await server.call_tool("list_tables", {})
            return result
            
        result = anyio.run(run_test)
        
        # Verify results - check that the call was successful
        assert result is not None
        mock_connection.execute_query.assert_called_once_with("SHOW TABLES")

    @patch('snowflake_mcp_server.server.SnowflakeConnection')
    @patch('snowflake_mcp_server.server.QueryValidator')
    def test_describe_table_tool(self, mock_validator_class, mock_connection_class) -> None:
        """Test describe_table tool functionality."""
        # Setup mocks
        mock_connection = AsyncMock()
        mock_validator = Mock()
        mock_connection_class.return_value = mock_connection
        mock_validator_class.return_value = mock_validator
        
        # Mock connection to return table description
        expected_description = [{"column": "id", "type": "NUMBER"}]
        mock_connection.execute_query.return_value = expected_description
        
        # Create server
        server = create_snowflake_mcp_server()
        
        # Test tool execution
        async def run_test():
            result = await server.call_tool("describe_table", {"table_name": "test_table"})
            return result
            
        result = anyio.run(run_test)
        
        # Verify results - check that the call was successful
        assert result is not None
        mock_connection.execute_query.assert_called_once_with("DESCRIBE TABLE test_table")

    @patch('snowflake_mcp_server.server.SnowflakeConnection')
    @patch('snowflake_mcp_server.server.QueryValidator')
    def test_get_schema_tool(self, mock_validator_class, mock_connection_class) -> None:
        """Test get_schema tool functionality."""
        # Setup mocks
        mock_connection = AsyncMock()
        mock_validator = Mock()
        mock_connection_class.return_value = mock_connection
        mock_validator_class.return_value = mock_validator
        
        # Mock connection to return schema info
        expected_schema = [{"schema_name": "PUBLIC"}]
        mock_connection.execute_query.return_value = expected_schema
        
        # Create server
        server = create_snowflake_mcp_server()
        
        # Test tool execution
        async def run_test():
            result = await server.call_tool("get_schema", {})
            return result
            
        result = anyio.run(run_test)
        
        # Verify results - check that the call was successful
        assert result is not None
        mock_connection.execute_query.assert_called_once_with("DESCRIBE SCHEMA")

    def test_server_has_all_expected_tools(self) -> None:
        """Test that server has all expected tools registered."""
        server = create_snowflake_mcp_server()
        
        async def get_tools():
            tools = await server.list_tools()
            return tools
            
        tools = anyio.run(get_tools)
        
        expected_tools = {"query", "list_tables", "describe_table", "get_schema"}
        actual_tools = {tool.name for tool in tools}
        
        assert expected_tools == actual_tools
