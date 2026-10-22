"""Настройка Django для тестов веб-части (без pytest-django).

Для тестов собирается отдельная временная база SQLite из data/*.json,
чтобы тесты не зависели от состояния рабочего data/weekly_menu.sqlite.
"""
import os
import tempfile
from pathlib import Path

TEST_DB = Path(tempfile.mkdtemp()) / "test_weekly_menu.sqlite"
os.environ["WEEKLY_MENU_DB"] = str(TEST_DB)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "weeklymenu.settings")

import django  # noqa: E402
from django.test.utils import setup_test_environment  # noqa: E402

from db import import_json  # noqa: E402

import_json.main(TEST_DB)
django.setup()
setup_test_environment()
