"""Пакет предметной области: блюда, пользователи, записи меню."""
from .dishes import Dish
from .menu import MenuEntry
from .users import User

__all__ = ["Dish", "MenuEntry", "User"]
