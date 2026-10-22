"""Сохранение и загрузка данных проекта в JSON-файлах.

В JSON хранятся только данные: у записи меню — идентификаторы блюда
и пользователя. При загрузке по ним восстанавливаются связи
между объектами, при сохранении объекты снова превращаются в словари.
"""
import json
from pathlib import Path
from typing import Any, List

from models import Dish, MenuEntry, User
from models.dishes import find_dish_by_id
from models.users import find_user_by_id

DATA_DIR = Path(__file__).resolve().parent / "data"
DISHES_FILE = DATA_DIR / "dishes.json"
USERS_FILE = DATA_DIR / "users.json"
MENU_FILE = DATA_DIR / "menu.json"


class StorageError(Exception):
    """Ошибка чтения данных: файл повреждён или имеет неверный вид."""


def read_json_list(filename: Path) -> List[dict]:
    """Прочитать JSON-файл со списком словарей.

    Если файла нет, возвращается пустой список. Если JSON некорректен,
    выбрасывается StorageError (файл при этом не затирается).
    """
    try:
        with open(filename, encoding="utf-8") as file:
            data: Any = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise StorageError(
            f"Файл {filename} содержит некорректный JSON: {error}"
        ) from error
    if not isinstance(data, list):
        raise StorageError(f"В файле {filename} ожидается список")
    return data


def write_json_list(filename: Path, items: List[dict]) -> None:
    """Записать список словарей в JSON-файл (каталог создаётся сам)."""
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(items, file, ensure_ascii=False, indent=2)


def load_dishes(filename: Path = DISHES_FILE) -> List[Dish]:
    """Загрузить блюда из JSON-файла в список объектов Dish."""
    try:
        return [Dish.from_data(item) for item in read_json_list(filename)]
    except (KeyError, TypeError) as error:
        raise StorageError(f"Неверные данные в {filename}") from error


def save_dishes(filename: Path, dishes: List[Dish]) -> None:
    """Сохранить объекты Dish в JSON-файл."""
    write_json_list(
        filename,
        [
            {
                "id": dish.id,
                "name": dish.name,
                "calories": dish.calories,
                "dish_type": dish.dish_type,
            }
            for dish in dishes
        ],
    )


def load_users(filename: Path = USERS_FILE) -> List[User]:
    """Загрузить пользователей из JSON-файла в список объектов User."""
    try:
        return [User.from_data(item) for item in read_json_list(filename)]
    except (KeyError, TypeError) as error:
        raise StorageError(f"Неверные данные в {filename}") from error


def save_users(filename: Path, users: List[User]) -> None:
    """Сохранить объекты User в JSON-файл."""
    write_json_list(
        filename,
        [
            {
                "id": user.id,
                "name": user.name,
                "goal": user.goal,
                "daily_limit": user.daily_limit,
            }
            for user in users
        ],
    )


def load_menu(
    filename: Path,
    dishes: List[Dish],
    users: List[User],
) -> List[MenuEntry]:
    """Загрузить записи меню и восстановить связи с блюдами и людьми.

    Если блюдо или пользователь с указанным идентификатором не найден,
    выбрасывается StorageError: корректный объект создать нельзя.
    """
    entries: List[MenuEntry] = []
    for item in read_json_list(filename):
        try:
            dish = find_dish_by_id(dishes, item["dish_id"])
            user = find_user_by_id(users, item["user_id"])
            if dish is None or user is None:
                raise StorageError(
                    f"Запись меню №{item['id']}: блюдо или пользователь "
                    "не найдены"
                )
            entry = MenuEntry(item["id"], dish, item["menu_date"], user)
            entry.is_cancelled = bool(item["is_cancelled"])
        except (KeyError, TypeError) as error:
            raise StorageError(f"Неверные данные в {filename}") from error
        entries.append(entry)
    return entries


def save_menu(filename: Path, entries: List[MenuEntry]) -> None:
    """Сохранить записи меню: объекты заменяются идентификаторами."""
    write_json_list(
        filename,
        [
            {
                "id": entry.id,
                "dish_id": entry.dish.id,
                "menu_date": entry.menu_date,
                "user_id": entry.user.id,
                "is_cancelled": entry.is_cancelled,
            }
            for entry in entries
        ],
    )
