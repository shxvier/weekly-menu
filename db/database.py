"""Подключение к базе данных SQLite проекта."""
import os
import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(
    os.environ.get("WEEKLY_MENU_DB", BASE_DIR / "data" / "weekly_menu.sqlite")
)
SCHEMA_FILE = BASE_DIR / "sql" / "schema.sql"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Открыть соединение с базой и включить проверку внешних ключей.

    row_factory = sqlite3.Row позволяет обращаться к полям строки
    результата по имени: row["name"] в Python, {{ row.name }} в шаблоне.
    """
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Создать таблицы по sql/schema.sql (повторный запуск безопасен)."""
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def fetch_all(sql: str, params: Iterable = ()) -> List[sqlite3.Row]:
    """Выполнить параметризованный SELECT и вернуть все строки."""
    conn = get_connection()
    try:
        return conn.execute(sql, tuple(params)).fetchall()
    finally:
        conn.close()


def fetch_one(sql: str, params: Iterable = ()) -> Optional[sqlite3.Row]:
    """Выполнить параметризованный SELECT и вернуть первую строку."""
    conn = get_connection()
    try:
        return conn.execute(sql, tuple(params)).fetchone()
    finally:
        conn.close()
