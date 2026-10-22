"""Страницы блюд: данные берутся из SQLite SQL-запросами."""
from django.shortcuts import render

from db.database import fetch_all, fetch_one

DISHES_ALL_SQL = """
    SELECT id, name, calories, dish_type
    FROM dishes
    ORDER BY name;
"""

DISHES_UP_TO_SQL = """
    SELECT id, name, calories, dish_type
    FROM dishes
    WHERE calories <= ?
    ORDER BY calories;
"""

DISH_BY_ID_SQL = """
    SELECT id, name, calories, dish_type
    FROM dishes
    WHERE id = ?;
"""

DISH_TIMES_PLANNED_SQL = """
    SELECT COUNT(*) AS times_planned
    FROM menu_entries
    WHERE dish_id = ?
        AND is_cancelled = 0;
"""


def parse_positive_int(value):
    """Вернуть положительное целое из строки запроса или None."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def dish_list(request):
    """Список блюд; с ?max_calories=N — только блюда не больше N ккал."""
    max_calories = parse_positive_int(request.GET.get("max_calories"))
    if max_calories is None:
        dishes = fetch_all(DISHES_ALL_SQL)
    else:
        dishes = fetch_all(DISHES_UP_TO_SQL, [max_calories])

    context = {
        "dishes": dishes,
        "max_calories": max_calories,
        "bad_input": bool(request.GET.get("max_calories"))
        and max_calories is None,
    }
    return render(request, "dishes/dish_list.html", context)


def dish_detail(request, dish_id):
    """Карточка блюда и число его появлений в активном меню."""
    dish = fetch_one(DISH_BY_ID_SQL, [dish_id])
    times_planned = 0
    if dish is not None:
        times_planned = fetch_one(
            DISH_TIMES_PLANNED_SQL, [dish_id]
        )["times_planned"]

    context = {
        "dish": dish,
        "times_planned": times_planned,
    }
    return render(
        request,
        "dishes/dish_detail.html",
        context,
        status=404 if dish is None else 200,
    )
