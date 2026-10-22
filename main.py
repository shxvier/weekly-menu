"""Консольное приложение «Сервис формирования меню на неделю» (ПР2)."""
from datetime import date

from dishes import (
    DISH_TYPES,
    add_dish,
    check_dish_calories,
    filter_dishes_by_calories,
    find_dish,
    sort_dishes,
)
from menu import (
    add_dish_to_day,
    cancel_menu_entry,
    check_day_calories,
    create_menu_entry,
    format_menu_line,
    get_day_calories,
    get_day_entries,
    get_week_fill,
)
from storage import (
    DISHES_FILE,
    MENU_FILE,
    StorageError,
    load_dishes,
    load_menu,
    save_dishes,
    save_menu,
)
from utils import (
    get_user_greeting,
    get_week_days,
    get_weekday_name,
    input_date,
    input_int,
)

# --- Данные пользователя (из ПР1) ---
USER_NAME = "Анна"
USER_GOAL = "поддержание веса"
MAX_CALORIES_PER_DAY = 2000

MENU_TEXT = """
=== Сервис формирования меню на неделю ===
1. Показать блюда
2. Найти блюдо по названию
3. Проверить калорийность блюда
4. Подобрать блюда по калорийности
5. Добавить новое блюдо
6. Добавить блюдо в меню на день
7. Убрать блюдо из меню
8. Показать меню на день
9. Показать заполненность недели
0. Выход"""


def show_dishes(dishes: list[dict]) -> None:
    """Вывести список блюд."""
    if not dishes:
        print("Блюда не найдены.")
        return
    for dish in dishes:
        print(
            f"{dish['id']:>3}. {dish['name']} — "
            f"{dish['calories']} ккал ({dish['dish_type']})"
        )


def show_day_menu(
    menu: list[dict],
    dishes: dict[int, dict],
    day: date,
) -> None:
    """Вывести меню на день, калорийность и статус лимита."""
    entries = get_day_entries(menu, day)
    day_label = f"{get_weekday_name(day)} ({day.strftime('%d.%m.%Y')})"
    names = ""
    for entry in entries:
        names = add_dish_to_day(names, dishes[entry["dish_id"]]["name"])
    calories = get_day_calories(menu, dishes, day)
    print(format_menu_line(day_label, names, calories))
    for entry in entries:
        dish = dishes[entry["dish_id"]]
        print(f"  №{entry['id']}: {dish['name']} ({dish['dish_type']})")
    if entries:
        print(check_day_calories(calories, MAX_CALORIES_PER_DAY))


def show_week_fill(menu: list[dict], dishes: dict[int, dict]) -> None:
    """Вывести заполненность дней недели."""
    day = input_date("Любая дата нужной недели: ")
    fill = get_week_fill(menu, get_week_days(day))
    for week_day, count in fill.items():
        calories = get_day_calories(menu, dishes, week_day)
        mark = "заполнен" if count else "пусто"
        print(
            f"{get_weekday_name(week_day):<12} {week_day:%d.%m}: "
            f"блюд {count}, {calories} ккал — {mark}"
        )


def ask_dish_id(dishes: dict[int, dict]) -> int:
    """Запросить номер существующего блюда."""
    while True:
        dish_id = input_int("Номер блюда: ")
        if dish_id in dishes:
            return dish_id
        print("Блюда с таким номером нет.")


def action_check_calories(dishes: dict[int, dict]) -> None:
    """Пункт меню: проверить калорийность блюда."""
    dish_id = ask_dish_id(dishes)
    limit = input_int("Максимум ккал на приём пищи: ", minimum=1)
    if check_dish_calories(dishes, dish_id, limit):
        print("Блюдо укладывается в лимит.")
    else:
        print("Блюдо превышает лимит.")


def action_filter(dishes: dict[int, dict]) -> None:
    """Пункт меню: отобрать блюда по калорийности и отсортировать."""
    limit = input_int("Не больше ккал: ", minimum=1)
    selected = filter_dishes_by_calories(dishes, limit)
    show_dishes(sort_dishes({d["id"]: d for d in selected}))


def action_add_dish(dishes: dict[int, dict]) -> None:
    """Пункт меню: добавить новое блюдо и сохранить файл."""
    name = input("Название блюда: ")
    calories = input_int("Калорийность, ккал: ", minimum=1)
    print("Тип блюда:", ", ".join(DISH_TYPES))
    dish_type = input("Тип: ").strip().lower()
    if dish_type not in DISH_TYPES:
        print("Неизвестный тип блюда.")
        return
    try:
        add_dish(dishes, name, calories, dish_type)
    except ValueError as error:
        print(f"Ошибка: {error}")
        return
    save_dishes(DISHES_FILE, dishes)
    print("Блюдо добавлено.")


def action_add_to_menu(
    menu: list[dict],
    dishes: dict[int, dict],
) -> None:
    """Пункт меню: добавить блюдо в меню на день и сохранить файл."""
    dish_id = ask_dish_id(dishes)
    day = input_date("Дата: ")
    entry = create_menu_entry(menu, dish_id, day)
    if entry is None:
        print("Это блюдо уже есть в меню на выбранный день.")
        return
    save_menu(MENU_FILE, menu)
    calories = get_day_calories(menu, dishes, day)
    print(f"Добавлено (запись №{entry['id']}).")
    print(check_day_calories(calories, MAX_CALORIES_PER_DAY))


def action_remove_from_menu(menu: list[dict]) -> None:
    """Пункт меню: убрать запись из меню и сохранить файл."""
    entry_id = input_int("Номер записи меню: ")
    if cancel_menu_entry(menu, entry_id):
        save_menu(MENU_FILE, menu)
        print("Запись убрана из меню.")
    else:
        print("Записи с таким номером нет.")


def run_menu(dishes: dict[int, dict], menu: list[dict]) -> None:
    """Главный цикл меню приложения."""
    while True:
        print(MENU_TEXT)
        choice = input("Выберите действие: ").strip()
        if choice == "1":
            show_dishes(list(dishes.values()))
        elif choice == "2":
            show_dishes(find_dish(dishes, input("Часть названия: ")))
        elif choice == "3":
            action_check_calories(dishes)
        elif choice == "4":
            action_filter(dishes)
        elif choice == "5":
            action_add_dish(dishes)
        elif choice == "6":
            action_add_to_menu(menu, dishes)
        elif choice == "7":
            action_remove_from_menu(menu)
        elif choice == "8":
            show_day_menu(menu, dishes, input_date("Дата: "))
        elif choice == "9":
            show_week_fill(menu, dishes)
        elif choice == "0":
            print("До встречи!")
            return
        else:
            print("Нет такого пункта меню.")


def main() -> None:
    """Точка входа: загрузка данных и запуск меню."""
    print(get_user_greeting(USER_NAME, USER_GOAL))
    print("-" * 40)
    try:
        dishes = load_dishes()
        menu = load_menu()
    except StorageError as error:
        print(f"Не удалось загрузить данные: {error}")
        return
    try:
        run_menu(dishes, menu)
    except (EOFError, KeyboardInterrupt):
        print("\nЗавершение работы.")


if __name__ == "__main__":
    main()
