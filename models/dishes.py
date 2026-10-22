"""Класс Dish и функции обработки коллекции блюд."""
from typing import Iterator, List, Optional

DISH_TYPES = ("завтрак", "обед", "ужин", "перекус")


class Dish:
    """Блюдо, которое можно включить в меню."""

    def __init__(
        self,
        dish_id: int,
        name: str,
        calories: int,
        dish_type: str,
    ) -> None:
        """Создать объект блюда."""
        self.id = dish_id
        self.name = name
        self.calories = calories
        self.dish_type = dish_type

    @staticmethod
    def validate_calories(calories: int) -> bool:
        """Проверить корректность калорийности (положительное число)."""
        return isinstance(calories, int) and calories > 0

    @classmethod
    def from_data(cls, data: dict) -> "Dish":
        """Создать блюдо из словаря данных (например, из JSON)."""
        return cls(
            dish_id=data["id"],
            name=data["name"],
            calories=data["calories"],
            dish_type=data["dish_type"],
        )

    def fits_limit(self, max_calories: int) -> bool:
        """Проверить, укладывается ли блюдо в лимит калорий."""
        return self.calories <= max_calories

    def __str__(self) -> str:
        """Вернуть строковое представление блюда."""
        return f"{self.name}, {self.calories} ккал ({self.dish_type})"


def add_dish(
    dishes: List[Dish],
    name: str,
    calories: int,
    dish_type: str,
) -> Dish:
    """Создать блюдо, добавить в коллекцию и вернуть его.

    Для пустого названия или неверной калорийности выбрасывается
    ValueError.
    """
    name = name.strip()
    if not name:
        raise ValueError("Название блюда не может быть пустым")
    if not Dish.validate_calories(calories):
        raise ValueError("Калорийность должна быть положительной")
    dish = Dish(
        max((item.id for item in dishes), default=0) + 1,
        name,
        calories,
        dish_type,
    )
    dishes.append(dish)
    return dish


def find_dish_by_id(dishes: List[Dish], dish_id: int) -> Optional[Dish]:
    """Найти блюдо по идентификатору."""
    for dish in dishes:
        if dish.id == dish_id:
            return dish
    return None


def find_dish(dishes: List[Dish], query: str) -> List[Dish]:
    """Найти блюда по подстроке названия (без учёта регистра)."""
    query = query.strip().casefold()
    return [dish for dish in dishes if query in dish.name.casefold()]


def check_dish_calories(
    dishes: List[Dish],
    dish_id: int,
    max_calories: int,
) -> bool:
    """Найти блюдо и проверить, укладывается ли оно в лимит калорий.

    Если блюда с таким идентификатором нет, выбрасывается KeyError.
    """
    dish = find_dish_by_id(dishes, dish_id)
    if dish is None:
        raise KeyError(dish_id)
    return dish.fits_limit(max_calories)


def iter_dishes_up_to(
    dishes: List[Dish],
    max_calories: int,
) -> Iterator[Dish]:
    """Генератор: отдаёт блюда, укладывающиеся в лимит калорий."""
    for dish in dishes:
        if dish.fits_limit(max_calories):
            yield dish


def filter_dishes_by_calories(
    dishes: List[Dish],
    max_calories: int,
) -> List[Dish]:
    """Отобрать блюда с калорийностью не больше max_calories."""
    return list(iter_dishes_up_to(dishes, max_calories))


def sort_dishes(
    dishes: List[Dish],
    by: str = "calories",
    reverse: bool = False,
) -> List[Dish]:
    """Отсортировать блюда по атрибуту by ('calories' или 'name')."""
    return sorted(
        dishes,
        key=lambda dish: getattr(dish, by),
        reverse=reverse,
    )


def show_dishes(dishes: List[Dish]) -> None:
    """Вывести список блюд."""
    if not dishes:
        print("Блюда не найдены.")
        return
    for dish in dishes:
        print(f"{dish.id:>3}. {dish}")
