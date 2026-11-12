"""Общие настройки тестов.

1. Для тестов SQL-слоя ПР7 собирается временная исходная база SQLite
   из data/*.json (переменная WEEKLY_MENU_DB), рабочий файл
   data/weekly_menu.sqlite не используется.
2. pytest-django создаёт тестовую базу Django миграциями; фикстура
   django_db_setup заполняет её скриптом переноса ПР9 из этой
   временной исходной базы.
"""
import os
import tempfile
from pathlib import Path

import pytest

SOURCE_DB = Path(tempfile.mkdtemp()) / "test_weekly_menu.sqlite"
os.environ["WEEKLY_MENU_DB"] = str(SOURCE_DB)

from db import import_json  # noqa: E402

import_json.main(SOURCE_DB)


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    from db import import_sqlite_to_orm

    with django_db_blocker.unblock():
        import_sqlite_to_orm.main(SOURCE_DB)
