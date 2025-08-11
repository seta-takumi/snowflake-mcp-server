"""クエリバリデーション (関数型スタイル)。

`is_read_only_query` という純関数を公開し、従来の `QueryValidator` クラスは
後方互換用の薄いアダプタとして保持する。
"""

from __future__ import annotations

from typing import Iterable, List, Sequence

READ_ONLY_STATEMENTS: Sequence[str] = (
    "SELECT",
    "SHOW",
    "DESCRIBE",
    "DESC",
    "EXPLAIN",
)


def normalize_query(query: str | None) -> str:
    """前後空白を除去し大文字化。None/空文字は空文字を返す (純関数)。"""
    if not query:
        return ""
    return query.strip().upper()


def is_read_only_query(query: str | None, read_only_prefixes: Iterable[str] = READ_ONLY_STATEMENTS) -> bool:
    """クエリが読み取り専用か判定する純関数。

    Args:
        query: 入力クエリ (None 可)
        read_only_prefixes: 判定対象となる先頭キーワード群 (デフォルト: READ_ONLY_STATEMENTS)
    """
    normalized = normalize_query(query)
    if not normalized:
        return False
    return any(normalized.startswith(prefix) for prefix in read_only_prefixes)


class QueryValidator:
    """後方互換のためのラッパ。新規コードは関数を直接利用推奨。"""

    def __init__(self) -> None:  # 保持 (インスタンス状態は不要)
        self._read_only_statements: List[str] = list(READ_ONLY_STATEMENTS)

    def is_read_only(self, query: str) -> bool:  # pragma: no cover (既存テストでカバー済)
        return is_read_only_query(query, self._read_only_statements)


__all__ = [
    "READ_ONLY_STATEMENTS",
    "normalize_query",
    "is_read_only_query",
    "QueryValidator",
]
