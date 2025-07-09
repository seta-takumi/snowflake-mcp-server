"""Test query validator functionality."""

from snowflake_mcp.query_validator import QueryValidator


class TestQueryValidator:
    """Test cases for query validation."""

    def test_select_query_is_read_only(self) -> None:
        """Test that SELECT queries are recognized as read-only."""
        validator = QueryValidator()
        query = "SELECT * FROM users"

        result = validator.is_read_only(query)

        assert result is True

    def test_insert_query_is_not_read_only(self) -> None:
        """Test that INSERT queries are rejected as write operations."""
        validator = QueryValidator()
        query = "INSERT INTO users (name) VALUES ('John')"

        result = validator.is_read_only(query)

        assert result is False

    def test_empty_query_is_not_read_only(self) -> None:
        """Test that empty queries return False for read-only check."""
        validator = QueryValidator()
        query = ""

        result = validator.is_read_only(query)

        assert result is False

    def test_whitespace_only_query_is_not_read_only(self) -> None:
        """Test that whitespace-only queries return False for read-only check."""
        validator = QueryValidator()
        query = "   \t\n  "

        result = validator.is_read_only(query)

        assert result is False

    def test_show_query_is_read_only(self) -> None:
        """Test that SHOW queries are recognized as read-only."""
        validator = QueryValidator()
        query = "SHOW TABLES"

        result = validator.is_read_only(query)

        assert result is True

    def test_describe_query_is_read_only(self) -> None:
        """Test that DESCRIBE queries are recognized as read-only."""
        validator = QueryValidator()
        query = "DESCRIBE TABLE users"

        result = validator.is_read_only(query)

        assert result is True

    def test_desc_query_is_read_only(self) -> None:
        """Test that DESC queries are recognized as read-only."""
        validator = QueryValidator()
        query = "DESC TABLE users"

        result = validator.is_read_only(query)

        assert result is True

    def test_explain_query_is_read_only(self) -> None:
        """Test that EXPLAIN queries are recognized as read-only."""
        validator = QueryValidator()
        query = "EXPLAIN SELECT * FROM users"

        result = validator.is_read_only(query)

        assert result is True

    def test_update_query_is_not_read_only(self) -> None:
        """Test that UPDATE queries are rejected as write operations."""
        validator = QueryValidator()
        query = "UPDATE users SET name = 'Jane' WHERE id = 1"

        result = validator.is_read_only(query)

        assert result is False

    def test_delete_query_is_not_read_only(self) -> None:
        """Test that DELETE queries are rejected as write operations."""
        validator = QueryValidator()
        query = "DELETE FROM users WHERE id = 1"

        result = validator.is_read_only(query)

        assert result is False

    def test_create_query_is_not_read_only(self) -> None:
        """Test that CREATE queries are rejected as write operations."""
        validator = QueryValidator()
        query = "CREATE TABLE test (id INT)"

        result = validator.is_read_only(query)

        assert result is False

    def test_drop_query_is_not_read_only(self) -> None:
        """Test that DROP queries are rejected as write operations."""
        validator = QueryValidator()
        query = "DROP TABLE test"

        result = validator.is_read_only(query)

        assert result is False

    def test_case_insensitive_select_query(self) -> None:
        """Test that case-insensitive SELECT queries are recognized as read-only."""
        validator = QueryValidator()
        query = "select * from users"

        result = validator.is_read_only(query)

        assert result is True

    def test_query_with_leading_whitespace(self) -> None:
        """Test that queries with leading whitespace are handled correctly."""
        validator = QueryValidator()
        query = "   SELECT * FROM users"

        result = validator.is_read_only(query)

        assert result is True

    def test_mixed_case_query(self) -> None:
        """Test that mixed case queries are handled correctly."""
        validator = QueryValidator()
        query = "SeLeCt * FrOm users"

        result = validator.is_read_only(query)

        assert result is True
