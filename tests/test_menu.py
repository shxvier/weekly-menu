from datetime import date

from models import Dish, MenuEntry, User
from models.menu import (
    add_dish_to_day,
    cancel_menu_entry,
    check_day_calories,
    create_menu_entry,
    find_entry_by_id,
    format_menu_line,
    get_day_calories,
    get_menu_status,
    get_week_fill,
    is_dish_available,
    is_dish_planned,
)

DAY = "2026-09-14"
ANNA = User(1, "Анна", "цель", 2000)
IVAN = User(2, "Иван", "цель", 2800)
PORRIDGE = Dish(1, "Каша", 300, "завтрак")
SOUP = Dish(2, "Суп", 400, "обед")


def test_entry_keeps_links_to_objects():
    entry = MenuEntry(1, PORRIDGE, DAY, ANNA)
    assert entry.dish is PORRIDGE
    assert entry.user.name == "Анна"
    assert entry.is_cancelled is False


def test_entry_str_shows_state():
    entry = MenuEntry(1, PORRIDGE, DAY, ANNA)
    assert "активно" in str(entry)
    entry.cancel()
    assert "отменено" in str(entry)


def test_create_returns_entry_and_blocks_duplicate():
    entries: list = []
    assert create_menu_entry(entries, PORRIDGE, ANNA, DAY) is not None
    assert not is_dish_available(entries, PORRIDGE, ANNA, DAY)
    assert create_menu_entry(entries, PORRIDGE, ANNA, DAY) is None
    assert len(entries) == 1


def test_other_user_can_plan_same_dish():
    entries: list = []
    create_menu_entry(entries, PORRIDGE, ANNA, DAY)
    assert is_dish_available(entries, PORRIDGE, IVAN, DAY)
    assert is_dish_planned(entries, PORRIDGE, DAY)
    assert not is_dish_planned(entries, PORRIDGE, DAY, IVAN)


def test_cancel_keeps_entry_but_unblocks_dish():
    entries: list = []
    entry = create_menu_entry(entries, PORRIDGE, ANNA, DAY)
    assert cancel_menu_entry(entries, entry.id)
    assert entry.is_cancelled
    assert entries == [entry]
    assert is_dish_available(entries, PORRIDGE, ANNA, DAY)
    assert not cancel_menu_entry(entries, entry.id)
    assert not cancel_menu_entry(entries, 99)
    assert find_entry_by_id(entries, entry.id) is entry


def test_day_calories_ignore_cancelled_and_other_users():
    entries: list = []
    create_menu_entry(entries, PORRIDGE, ANNA, DAY)
    soup = create_menu_entry(entries, SOUP, ANNA, DAY)
    create_menu_entry(entries, SOUP, IVAN, DAY)
    assert get_day_calories(entries, ANNA, DAY) == 700
    soup.cancel()
    assert get_day_calories(entries, ANNA, DAY) == 300


def test_week_fill():
    entries: list = []
    create_menu_entry(entries, PORRIDGE, ANNA, DAY)
    fill = get_week_fill(entries, ANNA, [date(2026, 9, 14),
                                         date(2026, 9, 15)])
    assert list(fill.values()) == [1, 0]


def test_texts():
    assert "можно" in get_menu_status(True)
    assert "уже есть" in get_menu_status(False)
    assert "Превышение лимита на 100" in check_day_calories(2100, 2000)
    assert add_dish_to_day("Каша", "Суп") == "Каша, Суп"
    assert "блюдо не выбрано" in format_menu_line("Пн", "", 0)
