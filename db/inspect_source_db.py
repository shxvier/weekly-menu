"""Инспекция исходной базы ПР7 (только чтение).

Запуск из корня проекта: python db/inspect_source_db.py
"""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DB = BASE_DIR / "data" / "weekly_menu.sqlite"


def main(source_db=SOURCE_DB):
    if not Path(source_db).exists():
        raise FileNotFoundError(f"Исходная база не найдена: {source_db}")
    with sqlite3.connect(source_db) as connection:
        connection.row_factory = sqlite3.Row
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
        for (table_name,) in tables:
            print(f"\nТаблица: {table_name}")
            print("Столбцы:")
            for column in connection.execute(
                f'PRAGMA table_info("{table_name}")'
            ):
                print(
                    f" имя={column['name']}, тип={column['type']}, "
                    f"NOT NULL={column['notnull']}, "
                    f"PRIMARY KEY={column['pk']}"
                )
            count = connection.execute(
                f'SELECT COUNT(*) FROM "{table_name}"'
            ).fetchone()[0]
            print(f"Количество записей: {count}")
        # Проверка ссылочной целостности записей меню.
        broken = connection.execute(
            """
            SELECT COUNT(*)
            FROM menu_entries
            WHERE dish_id NOT IN (SELECT id FROM dishes)
               OR user_id NOT IN (SELECT id FROM users)
            """
        ).fetchone()[0]
        print(f"\nЗаписей меню с битыми ссылками: {broken}")


if __name__ == "__main__":
    main()
