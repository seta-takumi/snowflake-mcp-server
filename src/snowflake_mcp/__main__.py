"""Main entry point for Snowflake MCP Server."""

import argparse
from mcp.server.fastmcp import FastMCP
from snowflake_mcp.connection import SnowflakeConnection
from snowflake_mcp.query_validator import QueryValidator
from typing import List, Dict, Any

# Global variables for components
connection = None
query_validator = None

def _is_read_only_query(query: str) -> bool:
    """Check if a query is read-only using the query validator."""
    return query_validator.is_read_only(query)

def create_server(connection_name: str = None) -> FastMCP:
    """Create and configure the FastMCP server."""
    global connection, query_validator
    
    # Initialize components
    connection = SnowflakeConnection(connection_name=connection_name)
    query_validator = QueryValidator()
    
    # Create the FastMCP server instance
    mcp = FastMCP("snowflake-mcp")
    
    @mcp.tool()
    async def query(sql: str) -> List[Dict[str, Any]]:
        """Execute read-only SQL queries on Snowflake."""
        if not _is_read_only_query(sql):
            raise ValueError("Only read-only queries are allowed")

        try:
            results = await connection.execute_query(sql)
            return results
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {str(e)}")

    @mcp.tool()
    async def list_tables() -> List[Dict[str, Any]]:
        """List all tables in the current schema."""
        try:
            results = await connection.execute_query("SHOW TABLES")
            return results
        except Exception as e:
            raise RuntimeError(f"Failed to list tables: {str(e)}")

    @mcp.tool()
    async def describe_table(table_name: str) -> List[Dict[str, Any]]:
        """Describe the structure of a table."""
        try:
            results = await connection.execute_query(f"DESCRIBE TABLE {table_name}")
            return results
        except Exception as e:
            raise RuntimeError(f"Failed to describe table: {str(e)}")

    @mcp.tool()
    async def get_schema() -> List[Dict[str, Any]]:
        """Get schema information."""
        try:
            results = await connection.execute_query("DESCRIBE SCHEMA")
            return results
        except Exception as e:
            raise RuntimeError(f"Failed to get schema: {str(e)}")
    
    return mcp

def main() -> None:
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(description="Snowflake MCP Server")
    parser.add_argument(
        "--connection-name",
        "-c",
        type=str,
        help="Connection name from connections.toml file"
    )
    
    args = parser.parse_args()
    
    # Create and run server with connection name
    mcp = create_server(connection_name=args.connection_name)
    mcp.run()

if __name__ == "__main__":
    main()
