"""クエリバリデーション (関数型スタイル)。

読み取り専用クエリの判定を行う純関数を提供する。
"""

from __future__ import annotations

from typing import Iterable, Sequence

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


__all__ = [
    "READ_ONLY_STATEMENTS",
    "normalize_query",
    "is_read_only_query",
]
