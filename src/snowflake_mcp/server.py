"""Snowflake MCP Server implementation."""

from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP
from .connection import SnowflakeConnection
from .query_validator import QueryValidator


class SnowflakeMCPServer:
    """Snowflake MCP Server for executing read-only queries."""

    def __init__(self) -> None:
        """Initialize the MCP server."""
        self.connection = SnowflakeConnection()
        self.query_validator = QueryValidator()
        self.server = FastMCP("snowflake-mcp")
        self._setup_tools()

    def _is_read_only_query(self, query: str) -> bool:
        """Check if a query is read-only using the query validator.

        Args:
            query: SQL query string to validate

        Returns:
            bool: True if query is read-only, False otherwise
        """
        return self.query_validator.is_read_only(query)

    def _setup_tools(self) -> None:
        """Set up MCP tools for the server."""

        @self.server.tool()
        async def query(sql: str) -> List[Dict[str, Any]]:
            """Execute read-only SQL queries on Snowflake."""
            return await self._query_tool(sql)

        @self.server.tool()
        async def list_tables() -> List[Dict[str, Any]]:
            """List all tables in the current schema."""
            return await self._list_tables_tool()

        @self.server.tool()
        async def describe_table(table_name: str) -> List[Dict[str, Any]]:
            """Describe the structure of a table."""
            return await self._describe_table_tool(table_name)

        @self.server.tool()
        async def get_schema() -> List[Dict[str, Any]]:
            """Get schema information."""
            return await self._get_schema_tool()

    async def _query_tool(self, sql: str) -> List[Dict[str, Any]]:
        """Execute a read-only SQL query.

        Args:
            sql: SQL query string to execute

        Returns:
            List[Dict[str, Any]]: Query results or error message
        """
        if not self._is_read_only_query(sql):
            raise ValueError("Only read-only queries are allowed")

        try:
            results = await self.connection.execute_query(sql)
            return results
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {str(e)}")

    async def _list_tables_tool(self) -> List[Dict[str, Any]]:
        """List all tables in the current schema.

        Returns:
            List[Dict[str, Any]]: List of tables or error message
        """
        try:
            results = await self.connection.execute_query("SHOW TABLES")
            return results
        except Exception as e:
            raise RuntimeError(f"Failed to list tables: {str(e)}")

    async def _describe_table_tool(self, table_name: str) -> List[Dict[str, Any]]:
        """Describe the structure of a table.

        Args:
            table_name: Name of the table to describe

        Returns:
            List[Dict[str, Any]]: Table structure or error message
        """
        try:
            results = await self.connection.execute_query(
                f"DESCRIBE TABLE {table_name}"
            )
            return results
        except Exception as e:
            raise RuntimeError(f"Failed to describe table: {str(e)}")

    async def _get_schema_tool(self) -> List[Dict[str, Any]]:
        """Get schema information.

        Returns:
            List[Dict[str, Any]]: Schema information or error message
        """
        try:
            results = await self.connection.execute_query("DESCRIBE SCHEMA")
            return results
        except Exception as e:
            raise RuntimeError(f"Failed to get schema: {str(e)}")

    def run(self) -> None:
        """Run the MCP server."""
        self.server.run()

    async def close(self) -> None:
        """Close the server and connections."""
        await self.connection.close()
