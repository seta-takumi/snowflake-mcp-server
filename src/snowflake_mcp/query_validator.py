"""Query validation functionality for Snowflake MCP Server."""

from typing import List


class QueryValidator:
    """Validates SQL queries for read-only operations."""

    def __init__(self) -> None:
        """Initialize query validator."""
        self._read_only_statements: List[str] = [
            "SELECT",
            "SHOW",
            "DESCRIBE",
            "DESC",
            "EXPLAIN",
        ]

    def is_read_only(self, query: str) -> bool:
        """Check if a query is read-only.

        Args:
            query: SQL query string to validate

        Returns:
            bool: True if query is read-only, False otherwise
        """
        if not query or not query.strip():
            return False

        query_upper = query.strip().upper()

        return any(query_upper.startswith(stmt) for stmt in self._read_only_statements)
