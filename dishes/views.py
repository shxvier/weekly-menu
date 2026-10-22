from datetime import date

from django.shortcuts import render

from models.dishes import find_dish_by_id
from models.menu import is_dish_planned
from storage import (
    DISHES_FILE,
    MENU_FILE,
    USERS_FILE,
    load_dishes,
    load_menu,
    load_users,
)


def dish_list(request):
    dishes = load_dishes(DISHES_FILE)

    context = {
        "dishes": dishes,
    }

    return render(request, "dishes/dish_list.html", context)


def dish_detail(request, dish_id):
    dishes = load_dishes(DISHES_FILE)
    dish = find_dish_by_id(dishes, dish_id)

    planned = False
    if dish is not None:
        users = load_users(USERS_FILE)
        entries = load_menu(MENU_FILE, dishes, users)
        planned = is_dish_planned(entries, dish, date.today().isoformat())

    context = {
        "dish": dish,
        "planned": planned,
    }

    return render(
        request,
        "dishes/dish_detail.html",
        context,
        status=404 if dish is None else 200,
    )
