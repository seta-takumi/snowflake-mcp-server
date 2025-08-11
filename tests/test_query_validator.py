"""Test query validator functionality."""

from snowflake_mcp_server.query_validator import (
    is_read_only_query,
    normalize_query,
    READ_ONLY_STATEMENTS,
)


# 旧クラスベースのテストは関数型 API へ統合済みのため削除


# --------------------------------------------------------------------------------------
# 関数型 API のテスト (新規推奨)
# --------------------------------------------------------------------------------------


class TestFunctionalQueryValidation:
    """関数型バリデーション API のテスト。純関数のため副作用なしでシンプル。"""

    def test_normalize_query_basic(self) -> None:
        """クエリの正規化テスト。"""
        assert normalize_query("  select * from table  ") == "SELECT * FROM TABLE"
        assert normalize_query("") == ""
        assert normalize_query(None) == ""
        assert normalize_query("   \t\n  ") == ""

    def test_is_read_only_query_select_variants(self) -> None:
        """SELECT系クエリの読み取り専用判定。"""
        assert is_read_only_query("SELECT * FROM users") is True
        assert is_read_only_query("  select id from table  ") is True
        assert is_read_only_query("SeLeCt COUNT(*) FROM orders") is True

    def test_is_read_only_query_show_variants(self) -> None:
        """SHOW系クエリの読み取り専用判定。"""
        assert is_read_only_query("SHOW TABLES") is True
        assert is_read_only_query("show databases") is True
        assert is_read_only_query("  SHOW COLUMNS FROM table  ") is True

    def test_is_read_only_query_describe_variants(self) -> None:
        """DESCRIBE/DESC系クエリの読み取り専用判定。"""
        assert is_read_only_query("DESCRIBE TABLE users") is True
        assert is_read_only_query("DESC table_name") is True
        assert is_read_only_query("describe schema") is True

    def test_is_read_only_query_explain(self) -> None:
        """EXPLAIN クエリの読み取り専用判定。"""
        assert is_read_only_query("EXPLAIN SELECT * FROM users") is True
        assert is_read_only_query("explain plan for select 1") is True

    def test_is_read_only_query_write_operations(self) -> None:
        """書き込み系クエリの判定。"""
        assert is_read_only_query("INSERT INTO users VALUES (1)") is False
        assert is_read_only_query("UPDATE users SET name='test'") is False
        assert is_read_only_query("DELETE FROM users") is False
        assert is_read_only_query("CREATE TABLE test (id INT)") is False
        assert is_read_only_query("DROP TABLE test") is False
        assert is_read_only_query("ALTER TABLE users ADD COLUMN age INT") is False

    def test_is_read_only_query_edge_cases(self) -> None:
        """エッジケースの判定。"""
        assert is_read_only_query("") is False
        assert is_read_only_query(None) is False
        assert is_read_only_query("   \t\n  ") is False
        assert is_read_only_query("INVALID_STATEMENT") is False

    def test_is_read_only_query_custom_prefixes(self) -> None:
        """カスタム接頭辞での判定テスト。"""
        custom_prefixes = ["CUSTOM", "TEST"]
        assert is_read_only_query("CUSTOM COMMAND", custom_prefixes) is True
        assert is_read_only_query("TEST QUERY", custom_prefixes) is True
        assert is_read_only_query("SELECT * FROM table", custom_prefixes) is False

    def test_read_only_statements_constant(self) -> None:
        """READ_ONLY_STATEMENTS 定数の内容確認。"""
        expected = {"SELECT", "SHOW", "DESCRIBE", "DESC", "EXPLAIN"}
        assert set(READ_ONLY_STATEMENTS) == expected
        # Sequence なので変更不可能性もテスト
        assert isinstance(READ_ONLY_STATEMENTS, tuple)
