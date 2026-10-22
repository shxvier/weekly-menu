"""Проверка схемы, импорта из JSON и SQL-запросов проекта."""
import json
import re
import sqlite3
from pathlib import Path

import pytest

from db import import_json
from db.database import DB_PATH, get_connection

QUERIES_FILE = Path(__file__).resolve().parent.parent / "sql" / "queries.sql"


def read_queries():
    """Разбить sql/queries.sql на пары (заголовок, текст запроса)."""
    text = QUERIES_FILE.read_text(encoding="utf-8")
    blocks = re.split(r"\n(?=-- Запрос \d+)", text)[1:]
    return [(b.splitlines()[0], b.split(";")[0]) for b in blocks]


def test_tables_and_foreign_keys():
    conn = get_connection()
    tables = {row["name"] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    )}
    assert {"dishes", "users", "menu_entries"} <= tables
    refs = {row["table"] for row in conn.execute(
        "PRAGMA foreign_key_list(menu_entries)"
    )}
    assert refs == {"dishes", "users"}
    conn.close()


@pytest.mark.parametrize("table, json_name", [
    ("dishes", "dishes.json"),
    ("users", "users.json"),
    ("menu_entries", "menu.json"),
])
def test_import_matches_json(table, json_name):
    expected = len(json.loads(
        (import_json.DATA_DIR / json_name).read_text(encoding="utf-8")
    ))
    conn = get_connection()
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    assert count == expected


def test_import_can_be_repeated():
    import_json.main(DB_PATH)
    conn = get_connection()
    assert conn.execute("SELECT COUNT(*) FROM dishes").fetchone()[0] == 9
    conn.close()


def test_foreign_keys_are_enforced():
    conn = get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO menu_entries (dish_id, user_id, menu_date) "
            "VALUES (999, 1, '2026-09-20')"
        )
    conn.close()


def test_queries_file_has_enough_queries():
    queries = read_queries()
    assert len(queries) >= 10
    text = " ".join(sql.upper() for _, sql in queries)
    for keyword in ("WHERE", "JOIN", "COUNT(", "GROUP BY", "HAVING"):
        assert text.count(keyword) >= 2, keyword


@pytest.mark.parametrize("title, sql", read_queries())
def test_every_query_runs(title, sql):
    conn = get_connection()
    conn.execute(sql).fetchall()
    conn.close()


def test_parameter_is_not_sql():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id FROM dishes WHERE name = ?",
        ["x' OR '1'='1"],
    ).fetchall()
    conn.close()
    assert rows == []
