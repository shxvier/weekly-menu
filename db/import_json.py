"""Перенос данных проекта из JSON-файлов в базу SQLite.

Запуск из корня проекта: python -m db.import_json

Скрипт создаёт таблицы (если их нет), очищает их и заново заполняет
данными из data/*.json — поэтому его можно запускать повторно.
Порядок важен: сначала блюда и пользователи, затем записи меню,
которые ссылаются на них внешними ключами.
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Optional

from db.database import BASE_DIR, DB_PATH, create_schema, get_connection

DATA_DIR = BASE_DIR / "data"
DISHES_FILE = DATA_DIR / "dishes.json"
USERS_FILE = DATA_DIR / "users.json"
MENU_FILE = DATA_DIR / "menu.json"


def load_json(filename: Path) -> List[dict]:
    """Прочитать список записей из JSON-файла."""
    with open(filename, encoding="utf-8") as file:
        return json.load(file)


def clear_tables(conn: sqlite3.Connection) -> None:
    """Очистить таблицы (сначала зависимую, потом справочники)."""
    conn.execute("DELETE FROM menu_entries")
    conn.execute("DELETE FROM users")
    conn.execute("DELETE FROM dishes")


def import_dishes(conn: sqlite3.Connection) -> None:
    """Перенести блюда."""
    conn.executemany(
        """
        INSERT INTO dishes (id, name, calories, dish_type)
        VALUES (?, ?, ?, ?)
        """,
        [
            (dish["id"], dish["name"], dish["calories"], dish["dish_type"])
            for dish in load_json(DISHES_FILE)
        ],
    )


def import_users(conn: sqlite3.Connection) -> None:
    """Перенести пользователей."""
    conn.executemany(
        """
        INSERT INTO users (id, name, goal, daily_limit)
        VALUES (?, ?, ?, ?)
        """,
        [
            (user["id"], user["name"], user.get("goal"),
             user["daily_limit"])
            for user in load_json(USERS_FILE)
        ],
    )


def import_menu(conn: sqlite3.Connection) -> None:
    """Перенести записи меню; bool из JSON превращается в 0/1."""
    conn.executemany(
        """
        INSERT INTO menu_entries
            (id, dish_id, user_id, menu_date, is_cancelled)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                entry["id"],
                entry["dish_id"],
                entry["user_id"],
                entry["menu_date"],
                int(entry["is_cancelled"]),
            )
            for entry in load_json(MENU_FILE)
        ],
    )


def main(db_path: Optional[Path] = None) -> None:
    """Создать схему и перенести все данные одной транзакцией."""
    conn = get_connection(db_path)
    try:
        create_schema(conn)
        clear_tables(conn)
        import_dishes(conn)
        import_users(conn)
        import_menu(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"Данные перенесены в {db_path or DB_PATH}")


if __name__ == "__main__":
    main()
