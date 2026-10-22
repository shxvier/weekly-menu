"""Страницы меню: данные берутся из SQLite SQL-запросами."""
from django.shortcuts import render

from db.database import fetch_all, fetch_one
from utils import parse_date

ACTIVE_ENTRIES_SQL = """
    SELECT
        menu_entries.id,
        menu_entries.menu_date,
        dishes.name AS dish_name,
        dishes.calories,
        users.name AS user_name,
        menu_entries.is_cancelled
    FROM menu_entries
    JOIN dishes
        ON menu_entries.dish_id = dishes.id
    JOIN users
        ON menu_entries.user_id = users.id
    WHERE menu_entries.is_cancelled = 0
    ORDER BY menu_entries.menu_date, users.name;
"""

ENTRY_BY_ID_SQL = """
    SELECT
        menu_entries.id,
        menu_entries.menu_date,
        menu_entries.is_cancelled,
        dishes.id AS dish_id,
        dishes.name AS dish_name,
        dishes.calories,
        dishes.dish_type,
        users.name AS user_name,
        users.daily_limit
    FROM menu_entries
    JOIN dishes
        ON menu_entries.dish_id = dishes.id
    JOIN users
        ON menu_entries.user_id = users.id
    WHERE menu_entries.id = ?;
"""

USERS_SQL = """
    SELECT id, name, goal, daily_limit
    FROM users
    ORDER BY name;
"""

USER_BY_ID_SQL = """
    SELECT id, name, goal, daily_limit
    FROM users
    WHERE id = ?;
"""

DAY_MENU_SQL = """
    SELECT
        menu_entries.id,
        dishes.name AS dish_name,
        dishes.dish_type,
        dishes.calories
    FROM menu_entries
    JOIN dishes
        ON menu_entries.dish_id = dishes.id
    WHERE menu_entries.user_id = ?
        AND menu_entries.menu_date = ?
        AND menu_entries.is_cancelled = 0
    ORDER BY dishes.calories;
"""

DAY_CALORIES_SQL = """
    SELECT COALESCE(SUM(dishes.calories), 0) AS day_calories
    FROM menu_entries
    JOIN dishes
        ON menu_entries.dish_id = dishes.id
    WHERE menu_entries.user_id = ?
        AND menu_entries.menu_date = ?
        AND menu_entries.is_cancelled = 0;
"""

FREE_DISHES_SQL = """
    SELECT id, name, calories, dish_type
    FROM dishes
    WHERE id NOT IN (
        SELECT dish_id
        FROM menu_entries
        WHERE user_id = ?
            AND menu_date = ?
            AND is_cancelled = 0
    )
    ORDER BY name;
"""

ENTRIES_COUNT_SQL = """
    SELECT
        COUNT(*) AS total_entries,
        SUM(is_cancelled = 0) AS active_entries,
        SUM(is_cancelled = 1) AS cancelled_entries
    FROM menu_entries;
"""

DISH_TYPES_SQL = """
    SELECT
        dish_type,
        COUNT(*) AS dishes_count,
        ROUND(AVG(calories)) AS avg_calories
    FROM dishes
    GROUP BY dish_type
    ORDER BY dishes_count DESC, dish_type;
"""

CALORIES_RANGE_SQL = """
    SELECT
        COUNT(*) AS dishes_count,
        MIN(calories) AS min_calories,
        MAX(calories) AS max_calories,
        ROUND(AVG(calories), 1) AS avg_calories
    FROM dishes;
"""

POPULARITY_SQL = """
    SELECT
        dishes.name AS dish_name,
        COUNT(menu_entries.id) AS times_planned
    FROM dishes
    LEFT JOIN menu_entries
        ON dishes.id = menu_entries.dish_id
        AND menu_entries.is_cancelled = 0
    GROUP BY dishes.id, dishes.name
    ORDER BY times_planned DESC, dishes.name;
"""

CALORIES_BY_DAY_SQL = """
    SELECT
        users.name AS user_name,
        menu_entries.menu_date,
        COUNT(*) AS dishes_count,
        SUM(dishes.calories) AS day_calories,
        users.daily_limit
    FROM menu_entries
    JOIN dishes
        ON menu_entries.dish_id = dishes.id
    JOIN users
        ON menu_entries.user_id = users.id
    WHERE menu_entries.is_cancelled = 0
    GROUP BY users.id, users.name, menu_entries.menu_date, users.daily_limit
    ORDER BY menu_entries.menu_date, users.name;
"""

OVER_LIMIT_SQL = """
    SELECT
        users.name AS user_name,
        menu_entries.menu_date,
        SUM(dishes.calories) AS day_calories,
        users.daily_limit,
        SUM(dishes.calories) - users.daily_limit AS excess
    FROM menu_entries
    JOIN dishes
        ON menu_entries.dish_id = dishes.id
    JOIN users
        ON menu_entries.user_id = users.id
    WHERE menu_entries.is_cancelled = 0
    GROUP BY users.id, users.name, menu_entries.menu_date, users.daily_limit
    HAVING SUM(dishes.calories) > users.daily_limit
    ORDER BY excess DESC;
"""

FREQUENT_DISHES_SQL = """
    SELECT
        dishes.name AS dish_name,
        COUNT(menu_entries.id) AS times_planned
    FROM dishes
    JOIN menu_entries
        ON dishes.id = menu_entries.dish_id
    WHERE menu_entries.is_cancelled = 0
    GROUP BY dishes.id, dishes.name
    HAVING COUNT(menu_entries.id) > ?
    ORDER BY times_planned DESC;
"""


def menu_list(request):
    """Активные записи меню (JOIN трёх таблиц) и счётчики записей."""
    context = {
        "entries": fetch_all(ACTIVE_ENTRIES_SQL),
        "counts": fetch_one(ENTRIES_COUNT_SQL),
    }
    return render(request, "menu/menu_list.html", context)


def menu_detail(request, entry_id):
    """Запись меню по id со связанными блюдом и пользователем."""
    entry = fetch_one(ENTRY_BY_ID_SQL, [entry_id])
    return render(
        request,
        "menu/menu_detail.html",
        {"entry": entry},
        status=404 if entry is None else 200,
    )


def day_menu(request):
    """Меню пользователя на дату: ?user=<id>&date=ГГГГ-ММ-ДД."""
    users = fetch_all(USERS_SQL)
    raw_date = request.GET.get("date", "")
    raw_user = request.GET.get("user", "")
    menu_date = parse_date(raw_date) if raw_date else None
    user = None
    if raw_user.isdigit():
        user = fetch_one(USER_BY_ID_SQL, [int(raw_user)])

    context = {
        "users": users,
        "selected_user": user,
        "date_value": menu_date.isoformat() if menu_date else raw_date,
        "error": None,
        "searched": False,
    }
    if raw_date or raw_user:
        if menu_date is None:
            context["error"] = "Укажите корректную дату."
        elif user is None:
            context["error"] = "Выберите пользователя."
    if menu_date is not None and user is not None:
        params = [user["id"], menu_date.isoformat()]
        day_calories = fetch_one(DAY_CALORIES_SQL, params)["day_calories"]
        context.update({
            "searched": True,
            "entries": fetch_all(DAY_MENU_SQL, params),
            "free_dishes": fetch_all(FREE_DISHES_SQL, params),
            "day_calories": day_calories,
            "left_calories": user["daily_limit"] - day_calories,
            "excess_calories": day_calories - user["daily_limit"],
        })
    return render(request, "menu/day_menu.html", context)


def statistics(request):
    """Статистика: агрегаты, GROUP BY и HAVING по меню и блюдам."""
    raw_threshold = request.GET.get("min_count", "2")
    threshold = int(raw_threshold) if raw_threshold.isdigit() else 2

    context = {
        "counts": fetch_one(ENTRIES_COUNT_SQL),
        "calories_range": fetch_one(CALORIES_RANGE_SQL),
        "dish_types": fetch_all(DISH_TYPES_SQL),
        "popularity": fetch_all(POPULARITY_SQL),
        "calories_by_day": fetch_all(CALORIES_BY_DAY_SQL),
        "over_limit": fetch_all(OVER_LIMIT_SQL),
        "frequent": fetch_all(FREQUENT_DISHES_SQL, [threshold]),
        "threshold": threshold,
    }
    return render(request, "menu/statistics.html", context)
