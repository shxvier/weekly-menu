"""Работа с меню: блюда по дням, проверка калорийности и повторов.

Меню — список словарей {"id", "dish_id", "menu_date"}; дата хранится
строкой ГГГГ-ММ-ДД. Блюдо нельзя добавить в один день дважды.
"""
from datetime import date
from typing import Optional


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


def is_dish_available(
    menu: list[dict],
    dish_id: int,
    menu_date: date,
) -> bool:
    """Проверить, можно ли добавить блюдо в меню на дату.

    Возвращает False, если блюдо уже есть в меню на эту дату.
    """
    iso_date = menu_date.isoformat()
    for entry in menu:
        if entry["dish_id"] == dish_id and entry["menu_date"] == iso_date:
            return False
    return True


def create_menu_entry(
    menu: list[dict],
    dish_id: int,
    menu_date: date,
) -> Optional[dict]:
    """Добавить блюдо в меню на дату.

    Возвращает созданную запись или None, если блюдо уже
    запланировано на этот день.
    """
    if not is_dish_available(menu, dish_id, menu_date):
        return None
    entry = {
        "id": max((item["id"] for item in menu), default=0) + 1,
        "dish_id": dish_id,
        "menu_date": menu_date.isoformat(),
    }
    menu.append(entry)
    return entry


def cancel_menu_entry(menu: list[dict], entry_id: int) -> bool:
    """Убрать запись из меню. Возвращает False, если записи нет."""
    for entry in menu:
        if entry["id"] == entry_id:
            menu.remove(entry)
            return True
    return False


def get_day_entries(menu: list[dict], menu_date: date) -> list[dict]:
    """Вернуть записи меню на указанную дату."""
    iso_date = menu_date.isoformat()
    return [entry for entry in menu if entry["menu_date"] == iso_date]


def get_day_calories(
    menu: list[dict],
    dishes: dict[int, dict],
    menu_date: date,
) -> int:
    """Суммарная калорийность блюд, запланированных на дату."""
    return sum(
        dishes[entry["dish_id"]]["calories"]
        for entry in get_day_entries(menu, menu_date)
    )


def get_week_fill(
    menu: list[dict],
    week_days: list[date],
) -> dict[date, int]:
    """Количество блюд в меню на каждый день недели."""
    return {day: len(get_day_entries(menu, day)) for day in week_days}
