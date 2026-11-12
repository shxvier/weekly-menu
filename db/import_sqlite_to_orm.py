"""Перенос данных из базы ПР7 в таблицы Django ORM.

Исходная база data/weekly_menu.sqlite не изменяется. Данные
записываются в базу Django (DATABASES["default"], db.sqlite3),
к которой уже применены миграции.

Запуск из корня проекта: python db/import_sqlite_to_orm.py
"""
import os
import sqlite3
import sys
from datetime import date
from pathlib import Path

import django
from django.db import transaction

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
SOURCE_DB = BASE_DIR / "data" / "weekly_menu.sqlite"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "weeklymenu.settings")
django.setup()

from dishes.models import Dish  # noqa: E402
from menu.models import MenuEntry  # noqa: E402
from users.models import User  # noqa: E402


def main(source_db=SOURCE_DB):
    if not Path(source_db).exists():
        raise FileNotFoundError(f"Исходная база не найдена: {source_db}")

    with sqlite3.connect(source_db) as connection:
        connection.row_factory = sqlite3.Row
        dishes = connection.execute(
            "SELECT id, name, calories, dish_type FROM dishes ORDER BY id"
        ).fetchall()
        users = connection.execute(
            "SELECT id, name, goal, daily_limit FROM users ORDER BY id"
        ).fetchall()
        entries = connection.execute(
            """
            SELECT id, dish_id, user_id, menu_date, is_cancelled
            FROM menu_entries
            ORDER BY id
            """
        ).fetchall()

    # Одна транзакция: при ошибке частичный перенос не сохранится.
    with transaction.atomic():
        # Сначала независимые сущности – блюда и пользователи.
        for row in dishes:
            Dish.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "name": row["name"],
                    "calories": row["calories"],
                    "dish_type": row["dish_type"],
                },
            )
        for row in users:
            User.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "name": row["name"],
                    # В ПР7 цель могла быть NULL; в модели – пустая строка.
                    "goal": row["goal"] or "",
                    "daily_limit": row["daily_limit"],
                },
            )
        # Затем записи меню, ссылающиеся на них внешними ключами.
        for row in entries:
            MenuEntry.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "dish_id": row["dish_id"],
                    "user_id": row["user_id"],
                    # Строка ГГГГ-ММ-ДД -> объект date для DateField.
                    "menu_date": date.fromisoformat(row["menu_date"]),
                    "is_cancelled": bool(row["is_cancelled"]),
                },
            )

    print("Перенос данных завершён.")
    print(f"Блюд: {Dish.objects.count()}")
    print(f"Пользователей: {User.objects.count()}")
    print(f"Записей меню: {MenuEntry.objects.count()}")


if __name__ == "__main__":
    main()
