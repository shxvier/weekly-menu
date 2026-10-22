import json

import pytest

from models import Dish, MenuEntry, User
from storage import (
    MENU_FILE,
    StorageError,
    load_dishes,
    load_menu,
    load_users,
    save_dishes,
    save_menu,
    save_users,
)

DISHES = [Dish(1, "Каша", 300, "завтрак"), Dish(2, "Суп", 400, "обед")]
USERS = [User(1, "Анна", "цель", 2000)]


def test_missing_files_give_empty_collections(tmp_path):
    missing = tmp_path / "none.json"
    assert load_dishes(missing) == []
    assert load_users(missing) == []
    assert load_menu(missing, DISHES, USERS) == []


def test_dishes_and_users_round_trip(tmp_path):
    save_dishes(tmp_path / "d.json", DISHES)
    save_users(tmp_path / "u.json", USERS)
    dishes = load_dishes(tmp_path / "d.json")
    users = load_users(tmp_path / "u.json")
    assert [d.name for d in dishes] == ["Каша", "Суп"]
    assert users[0].daily_limit == 2000


def test_menu_saves_ids_and_restores_links(tmp_path):
    path = tmp_path / "m.json"
    entry = MenuEntry(1, DISHES[1], "2026-09-14", USERS[0])
    entry.cancel()
    save_menu(path, [entry])
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw == [{"id": 1, "dish_id": 2, "menu_date": "2026-09-14",
                    "user_id": 1, "is_cancelled": True}]
    loaded = load_menu(path, DISHES, USERS)[0]
    assert loaded.dish is DISHES[1]
    assert loaded.user is USERS[0]
    assert loaded.is_cancelled is True


def test_menu_with_unknown_dish_is_error(tmp_path):
    path = tmp_path / "m.json"
    path.write_text(json.dumps([{
        "id": 1, "dish_id": 99, "menu_date": "2026-09-14",
        "user_id": 1, "is_cancelled": False,
    }]), encoding="utf-8")
    with pytest.raises(StorageError):
        load_menu(path, DISHES, USERS)


def test_broken_json_raises_storage_error(tmp_path):
    path = tmp_path / "d.json"
    path.write_text("[не json", encoding="utf-8")
    with pytest.raises(StorageError):
        load_dishes(path)
    path.write_text(json.dumps([{"id": 1}]), encoding="utf-8")
    with pytest.raises(StorageError):
        load_dishes(path)


def test_real_data_files_are_consistent():
    dishes = load_dishes()
    users = load_users()
    entries = load_menu(MENU_FILE, dishes, users)
    assert dishes and users and entries
