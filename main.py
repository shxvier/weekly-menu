"""Консольное приложение «Сервис формирования меню на неделю» (ПР3).

Данные приложения — коллекции объектов Dish, User и MenuEntry.
"""
from typing import List

from models import Dish, MenuEntry, User
from models.dishes import (
    DISH_TYPES,
    add_dish,
    check_dish_calories,
    filter_dishes_by_calories,
    find_dish,
    find_dish_by_id,
    show_dishes,
    sort_dishes,
)
from models.menu import (
    add_dish_to_day,
    cancel_menu_entry,
    check_day_calories,
    create_menu_entry,
    format_menu_line,
    get_day_calories,
    get_day_entries,
    get_menu_status,
    get_week_fill,
    is_dish_available,
    show_menu,
)
from models.users import add_user, find_user_by_id, show_users
from storage import (
    DISHES_FILE,
    MENU_FILE,
    USERS_FILE,
    StorageError,
    load_dishes,
    load_menu,
    load_users,
    save_dishes,
    save_menu,
    save_users,
)
from utils import (
    get_user_greeting,
    get_week_days,
    get_weekday_name,
    input_date,
    input_int,
)

MENU_TEXT = """
=== Сервис формирования меню на неделю ===
1. Показать блюда
2. Найти блюдо по названию
3. Проверить калорийность блюда
4. Подобрать блюда по калорийности
5. Добавить новое блюдо
6. Добавить блюдо в меню на день
7. Отменить блюдо в меню
8. Показать меню на день
9. Показать заполненность недели
10. Показать все записи меню
11. Показать пользователей
12. Добавить пользователя
13. Сменить пользователя
0. Выход"""


def save_all(
    dishes: List[Dish],
    users: List[User],
    entries: List[MenuEntry],
) -> None:
    """Сохранить все коллекции в JSON-файлы."""
    save_dishes(DISHES_FILE, dishes)
    save_users(USERS_FILE, users)
    save_menu(MENU_FILE, entries)


def ask_dish(dishes: List[Dish]) -> Dish:
    """Запросить номер блюда, пока не найдено существующее."""
    while True:
        dish = find_dish_by_id(dishes, input_int("Номер блюда: "))
        if dish is not None:
            return dish
        print("Блюда с таким номером нет.")


def ask_user(users: List[User]) -> User:
    """Запросить номер пользователя, пока не найден существующий."""
    while True:
        user = find_user_by_id(users, input_int("Номер пользователя: "))
        if user is not None:
            return user
        print("Пользователя с таким номером нет.")


def show_day_menu(
    entries: List[MenuEntry],
    user: User,
    menu_date: str,
) -> None:
    """Вывести меню пользователя на день и оценку калорийности."""
    day_entries = get_day_entries(entries, user, menu_date)
    names = ""
    for entry in day_entries:
        names = add_dish_to_day(names, entry.dish.name)
    calories = get_day_calories(entries, user, menu_date)
    print(format_menu_line(menu_date, names, calories))
    for entry in day_entries:
        print(f"  №{entry.id}: {entry.dish}")
    if day_entries:
        print(check_day_calories(calories, user.daily_limit))


def action_show_day(entries: List[MenuEntry], user: User) -> None:
    """Пункт меню: показать меню на выбранный день."""
    day = input_date("Дата: ")
    show_day_menu(entries, user, day.isoformat())


def show_week_fill(entries: List[MenuEntry], user: User) -> None:
    """Вывести заполненность дней недели для пользователя."""
    day = input_date("Любая дата нужной недели: ")
    fill = get_week_fill(entries, user, get_week_days(day))
    for week_day, count in fill.items():
        calories = get_day_calories(entries, user, week_day.isoformat())
        mark = "заполнен" if count else "пусто"
        print(
            f"{get_weekday_name(week_day):<12} {week_day:%d.%m}: "
            f"блюд {count}, {calories} ккал — {mark}"
        )


def action_check_calories(dishes: List[Dish]) -> None:
    """Пункт меню: проверить калорийность блюда."""
    dish = ask_dish(dishes)
    limit = input_int("Максимум ккал на приём пищи: ", minimum=1)
    if check_dish_calories(dishes, dish.id, limit):
        print("Блюдо укладывается в лимит.")
    else:
        print("Блюдо превышает лимит.")


def action_filter(dishes: List[Dish]) -> None:
    """Пункт меню: отобрать блюда по калорийности и отсортировать."""
    limit = input_int("Не больше ккал: ", minimum=1)
    show_dishes(sort_dishes(filter_dishes_by_calories(dishes, limit)))


def action_add_dish(dishes: List[Dish]) -> bool:
    """Пункт меню: добавить блюдо. True, если коллекция изменилась."""
    name = input("Название блюда: ")
    calories = input_int("Калорийность, ккал: ", minimum=1)
    print("Тип блюда:", ", ".join(DISH_TYPES))
    dish_type = input("Тип: ").strip().lower()
    if dish_type not in DISH_TYPES:
        print("Неизвестный тип блюда.")
        return False
    try:
        dish = add_dish(dishes, name, calories, dish_type)
    except ValueError as error:
        print(f"Ошибка: {error}")
        return False
    print(f"Блюдо добавлено: №{dish.id}.")
    return True


def create_new_menu_entry(
    entries: List[MenuEntry],
    dishes: List[Dish],
    user: User,
) -> bool:
    """Сценарий добавления блюда в меню. True, если запись создана."""
    dish = ask_dish(dishes)
    day = input_date("Дата: ").isoformat()
    available = is_dish_available(entries, dish, user, day)
    print(get_menu_status(available))
    entry = create_menu_entry(entries, dish, user, day)
    if entry is None:
        return False
    print(f"Добавлено (запись №{entry.id}).")
    calories = get_day_calories(entries, user, day)
    print(check_day_calories(calories, user.daily_limit))
    return True


def action_cancel_entry(entries: List[MenuEntry]) -> bool:
    """Пункт меню: отменить запись меню. True, если она отменена."""
    entry_id = input_int("Номер записи меню: ")
    if cancel_menu_entry(entries, entry_id):
        print("Блюдо убрано из меню.")
        return True
    print("Активной записи с таким номером нет.")
    return False


def action_add_user(users: List[User]) -> bool:
    """Пункт меню: добавить пользователя. True, если добавлен."""
    name = input("Имя: ")
    goal = input("Цель: ")
    limit = input_int("Лимит калорий в день: ", minimum=1)
    try:
        user = add_user(users, name, goal, limit)
    except ValueError as error:
        print(f"Ошибка: {error}")
        return False
    print(f"Пользователь добавлен: №{user.id}.")
    return True


def run_menu(
    dishes: List[Dish],
    users: List[User],
    entries: List[MenuEntry],
    user: User,
) -> None:
    """Главный цикл меню; после каждого изменения данные сохраняются."""
    while True:
        print(MENU_TEXT)
        print(f"Текущий пользователь: {user.name}")
        choice = input("Выберите действие: ").strip()
        changed = False
        if choice == "1":
            show_dishes(dishes)
        elif choice == "2":
            show_dishes(find_dish(dishes, input("Часть названия: ")))
        elif choice == "3":
            action_check_calories(dishes)
        elif choice == "4":
            action_filter(dishes)
        elif choice == "5":
            changed = action_add_dish(dishes)
        elif choice == "6":
            changed = create_new_menu_entry(entries, dishes, user)
        elif choice == "7":
            changed = action_cancel_entry(entries)
        elif choice == "8":
            action_show_day(entries, user)
        elif choice == "9":
            show_week_fill(entries, user)
        elif choice == "10":
            show_menu(entries)
        elif choice == "11":
            show_users(users)
        elif choice == "12":
            changed = action_add_user(users)
        elif choice == "13":
            user = ask_user(users)
        elif choice == "0":
            print("До встречи!")
            return
        else:
            print("Нет такого пункта меню.")
        if changed:
            save_all(dishes, users, entries)


def main() -> None:
    """Точка входа: загрузка данных, выбор пользователя, меню."""
    try:
        dishes = load_dishes()
        users = load_users()
        entries = load_menu(MENU_FILE, dishes, users)
    except StorageError as error:
        print(f"Не удалось загрузить данные: {error}")
        return
    if not users:
        print("Нет пользователей. Добавьте их в data/users.json.")
        return
    user = users[0]
    print(get_user_greeting(user.name, user.goal))
    print("-" * 40)
    try:
        run_menu(dishes, users, entries, user)
    except (EOFError, KeyboardInterrupt):
        print("\nЗавершение работы.")
    finally:
        save_all(dishes, users, entries)


if __name__ == "__main__":
    main()
