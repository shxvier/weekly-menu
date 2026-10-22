import json

import pytest

from storage import (
    StorageError,
    load_dishes,
    load_menu,
    save_dishes,
    save_menu,
)


def test_missing_file_gives_empty_data(tmp_path):
    assert load_dishes(tmp_path / "none.json") == {}
    assert load_menu(tmp_path / "none.json") == []


def test_dishes_round_trip(tmp_path):
    path = tmp_path / "data" / "dishes.json"
    dishes = {1: {"id": 1, "name": "Каша", "calories": 300,
                  "dish_type": "завтрак"}}
    save_dishes(path, dishes)
    assert load_dishes(path) == dishes


def test_menu_round_trip(tmp_path):
    path = tmp_path / "menu.json"
    menu = [{"id": 1, "dish_id": 1, "menu_date": "2026-09-14"}]
    save_menu(path, menu)
    assert load_menu(path) == menu


def test_broken_json_raises_storage_error(tmp_path):
    path = tmp_path / "dishes.json"
    path.write_text("{не json", encoding="utf-8")
    with pytest.raises(StorageError):
        load_dishes(path)


def test_wrong_structure_raises_storage_error(tmp_path):
    path = tmp_path / "dishes.json"
    path.write_text(json.dumps({"a": 1}), encoding="utf-8")
    with pytest.raises(StorageError):
        load_dishes(path)
    path.write_text(json.dumps([{"name": "без id"}]), encoding="utf-8")
    with pytest.raises(StorageError):
        load_dishes(path)
