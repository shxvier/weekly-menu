"""Класс MenuEntry и функции работы с меню на неделю.

Запись меню связывает блюдо и пользователя с датой. Отмена записи
не удаляет её из коллекции: меняется только признак is_cancelled,
а отменённая запись перестаёт учитываться в меню.
"""
from datetime import date
from typing import Dict, List, Optional

from .dishes import Dish
from .users import User


class MenuEntry:
    """Запись меню: блюдо, добавленное пользователем на дату."""

    def __init__(
        self,
        entry_id: int,
        dish: Dish,
        menu_date: str,
        user: User,
    ) -> None:
        """Создать запись меню (дата — строка ГГГГ-ММ-ДД)."""
        self.id = entry_id
        self.dish = dish
        self.menu_date = menu_date
        self.user = user
        self.is_cancelled = False

    def cancel(self) -> None:
        """Отменить запись меню (объект остаётся в коллекции)."""
        self.is_cancelled = True

    def __str__(self) -> str:
        """Вернуть строковое представление записи меню."""
        state = "отменено" if self.is_cancelled else "активно"
        return (
            f"№{self.id}: {self.menu_date} — {self.dish.name} "
            f"({self.user.name}) [{state}]"
        )


def add_dish_to_day(current_dish: str, new_dish: str) -> str:
    """Добавляет блюдо в день, если он ещё пуст."""
    if current_dish == "":
        return new_dish
    return f"{current_dish}, {new_dish}"


def check_day_calories(calories: int, limit: int) -> str:
    """Проверяет, укладывается ли день в лимит калорий."""
    if calories > limit:
        return f"Превышение лимита на {calories - limit} ккал"
    return f"В пределах нормы (осталось {limit - calories} ккал)"


def format_menu_line(day: str, dish: str, calories: int) -> str:
    """Формирует строку меню для вывода."""
    if dish == "":
        return f"{day}: блюдо не выбрано"
    return f"{day}: {dish} — {calories} ккал"


def is_dish_planned(
    entries: List[MenuEntry],
    dish: Dish,
    menu_date: str,
    user: Optional[User] = None,
) -> bool:
    """Есть ли активная запись с блюдом на дату.

    Если задан user, учитываются только записи этого пользователя.
    """
    for entry in entries:
        if entry.is_cancelled or entry.menu_date != menu_date:
            continue
        if entry.dish.id != dish.id:
            continue
        if user is None or entry.user.id == user.id:
            return True
    return False


def is_dish_available(
    entries: List[MenuEntry],
    dish: Dish,
    user: User,
    menu_date: str,
) -> bool:
    """Можно ли добавить блюдо в меню пользователя на дату.

    Активная запись блокирует блюдо на этот день, отменённая — нет.
    """
    return not is_dish_planned(entries, dish, menu_date, user)


def create_menu_entry(
    entries: List[MenuEntry],
    dish: Dish,
    user: User,
    menu_date: str,
) -> Optional[MenuEntry]:
    """Создать запись меню и добавить её в коллекцию.

    Возвращает None, если блюдо уже есть в меню пользователя на дату.
    """
    if not is_dish_available(entries, dish, user, menu_date):
        return None
    entry = MenuEntry(
        max((item.id for item in entries), default=0) + 1,
        dish,
        menu_date,
        user,
    )
    entries.append(entry)
    return entry


def find_entry_by_id(
    entries: List[MenuEntry],
    entry_id: int,
) -> Optional[MenuEntry]:
    """Найти запись меню по идентификатору."""
    for entry in entries:
        if entry.id == entry_id:
            return entry
    return None


def cancel_menu_entry(entries: List[MenuEntry], entry_id: int) -> bool:
    """Отменить запись меню. False — записи нет или она уже отменена."""
    entry = find_entry_by_id(entries, entry_id)
    if entry is None or entry.is_cancelled:
        return False
    entry.cancel()
    return True


def get_menu_status(is_available: bool) -> str:
    """Вернуть текстовый статус блюда для выбранного дня."""
    if is_available:
        return "Блюдо можно добавить в меню на этот день"
    return "Блюдо уже есть в меню на этот день"


def get_day_entries(
    entries: List[MenuEntry],
    user: User,
    menu_date: str,
) -> List[MenuEntry]:
    """Активные записи меню пользователя на дату."""
    return [
        entry for entry in entries
        if not entry.is_cancelled
        and entry.user.id == user.id
        and entry.menu_date == menu_date
    ]


def get_day_calories(
    entries: List[MenuEntry],
    user: User,
    menu_date: str,
) -> int:
    """Суммарная калорийность меню пользователя на дату."""
    return sum(
        entry.dish.calories
        for entry in get_day_entries(entries, user, menu_date)
    )


def get_week_fill(
    entries: List[MenuEntry],
    user: User,
    week_days: List[date],
) -> Dict[date, int]:
    """Количество блюд в меню пользователя на каждый день недели."""
    return {
        day: len(get_day_entries(entries, user, day.isoformat()))
        for day in week_days
    }


def show_menu(entries: List[MenuEntry]) -> None:
    """Вывести записи меню."""
    if not entries:
        print("Записей меню нет.")
        return
    for entry in entries:
        print(entry)
