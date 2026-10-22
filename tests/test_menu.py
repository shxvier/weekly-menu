from datetime import date

from menu import (
    add_dish_to_day,
    cancel_menu_entry,
    check_day_calories,
    create_menu_entry,
    format_menu_line,
    get_day_calories,
    get_week_fill,
    is_dish_available,
)

MONDAY = date(2026, 9, 14)
TUESDAY = date(2026, 9, 15)
DISHES = {
    1: {"id": 1, "name": "Каша", "calories": 300, "dish_type": "завтрак"},
    2: {"id": 2, "name": "Суп", "calories": 400, "dish_type": "обед"},
}


def test_is_dish_available_on_empty_menu():
    assert is_dish_available([], 1, MONDAY)


def test_duplicate_dish_forbidden():
    menu: list = []
    assert create_menu_entry(menu, 1, MONDAY) is not None
    assert not is_dish_available(menu, 1, MONDAY)
    assert create_menu_entry(menu, 1, MONDAY) is None
    assert len(menu) == 1


def test_same_dish_on_other_day_allowed():
    menu: list = []
    create_menu_entry(menu, 1, MONDAY)
    assert create_menu_entry(menu, 1, TUESDAY) is not None


def test_cancel_menu_entry():
    menu: list = []
    entry = create_menu_entry(menu, 1, MONDAY)
    assert cancel_menu_entry(menu, entry["id"])
    assert menu == []
    assert not cancel_menu_entry(menu, 99)


def test_get_day_calories():
    menu: list = []
    create_menu_entry(menu, 1, MONDAY)
    create_menu_entry(menu, 2, MONDAY)
    assert get_day_calories(menu, DISHES, MONDAY) == 700
    assert get_day_calories(menu, DISHES, TUESDAY) == 0


def test_get_week_fill():
    menu: list = []
    create_menu_entry(menu, 1, MONDAY)
    assert get_week_fill(menu, [MONDAY, TUESDAY]) == {MONDAY: 1, TUESDAY: 0}


def test_day_calories_status():
    assert "Превышение лимита на 100" in check_day_calories(2100, 2000)
    assert "осталось 500" in check_day_calories(1500, 2000)


def test_menu_line_helpers():
    assert add_dish_to_day("", "Каша") == "Каша"
    assert add_dish_to_day("Каша", "Суп") == "Каша, Суп"
    assert "блюдо не выбрано" in format_menu_line("Пн", "", 0)
    assert format_menu_line("Пн", "Каша", 300) == "Пн: Каша — 300 ккал"
