"""Работа с блюдами: добавление, поиск, отбор и сортировка.

Блюда хранятся в словаре: ключ — идентификатор блюда, значение —
словарь с данными блюда (id, name, calories, dish_type).
"""
from typing import Iterator

DISH_TYPES = ("завтрак", "обед", "ужин", "перекус")


def add_dish(
    dishes: dict[int, dict],
    name: str,
    calories: int,
    dish_type: str,
) -> None:
    """Добавить блюдо в словарь dishes.

    Идентификатор формируется как максимальный существующий плюс один.
    Для пустого названия или неположительной калорийности
    выбрасывается ValueError.
    """
    name = name.strip()
    if not name:
        raise ValueError("Название блюда не может быть пустым")
    if calories <= 0:
        raise ValueError("Калорийность должна быть положительной")
    dish_id = max(dishes, default=0) + 1
    dishes[dish_id] = {
        "id": dish_id,
        "name": name,
        "calories": calories,
        "dish_type": dish_type,
    }


def find_dish(dishes: dict[int, dict], query: str) -> list[dict]:
    """Найти блюда по подстроке названия (без учёта регистра)."""
    query = query.strip().casefold()
    return [
        dish for dish in dishes.values()
        if query in dish["name"].casefold()
    ]


def check_dish_calories(
    dishes: dict[int, dict],
    dish_id: int,
    max_calories: int,
) -> bool:
    """Проверить, укладывается ли блюдо в лимит калорий.

    Возвращает True, если калорийность блюда не больше max_calories.
    Если блюда нет, выбрасывается KeyError.
    """
    return dishes[dish_id]["calories"] <= max_calories


def iter_dishes_up_to(
    dishes: dict[int, dict],
    max_calories: int,
) -> Iterator[dict]:
    """Генератор: отдаёт блюда с калорийностью не больше лимита."""
    for dish in dishes.values():
        if dish["calories"] <= max_calories:
            yield dish


def filter_dishes_by_calories(
    dishes: dict[int, dict],
    max_calories: int,
) -> list[dict]:
    """Отобрать блюда с калорийностью не больше max_calories."""
    return list(iter_dishes_up_to(dishes, max_calories))


def sort_dishes(
    dishes: dict[int, dict],
    by: str = "calories",
    reverse: bool = False,
) -> list[dict]:
    """Отсортировать блюда по полю by ('calories' или 'name')."""
    return sorted(
        dishes.values(),
        key=lambda dish: dish[by],
        reverse=reverse,
    )
