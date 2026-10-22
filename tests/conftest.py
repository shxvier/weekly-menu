"""Настройка Django для тестов веб-части (без pytest-django)."""
import os

import django
from django.test.utils import setup_test_environment

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "weeklymenu.settings")
django.setup()
setup_test_environment()
