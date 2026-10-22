"""Сохранение и загрузка данных проекта в JSON-файлах."""
import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"
DISHES_FILE = DATA_DIR / "dishes.json"
MENU_FILE = DATA_DIR / "menu.json"


class StorageError(Exception):
    """Ошибка чтения данных: файл повреждён или имеет неверный вид."""


def read_json_list(filename: Path) -> list[dict]:
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


def write_json_list(filename: Path, items: list[dict]) -> None:
    """Записать список словарей в JSON-файл (каталог создаётся сам)."""
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(items, file, ensure_ascii=False, indent=2)


def load_dishes(filename: Path = DISHES_FILE) -> dict[int, dict]:
    """Загрузить блюда из JSON-файла в словарь {id: данные}."""
    try:
        return {item["id"]: item for item in read_json_list(filename)}
    except (KeyError, TypeError) as error:
        raise StorageError(f"Неверные данные в {filename}") from error


def save_dishes(filename: Path, dishes: dict[int, dict]) -> None:
    """Сохранить блюда в JSON-файл."""
    write_json_list(filename, list(dishes.values()))


def load_menu(filename: Path = MENU_FILE) -> list[dict]:
    """Загрузить записи меню из JSON-файла."""
    return read_json_list(filename)


def save_menu(filename: Path, menu: list[dict]) -> None:
    """Сохранить записи меню в JSON-файл."""
    write_json_list(filename, menu)
