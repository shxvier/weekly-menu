from django.shortcuts import render

from models.menu import find_entry_by_id
from storage import (
    DISHES_FILE,
    MENU_FILE,
    USERS_FILE,
    load_dishes,
    load_menu,
    load_users,
)


def load_entries():
    dishes = load_dishes(DISHES_FILE)
    users = load_users(USERS_FILE)
    return load_menu(MENU_FILE, dishes, users)


def menu_list(request):
    context = {
        "entries": load_entries(),
    }

    return render(request, "menu/menu_list.html", context)


def menu_detail(request, entry_id):
    entry = find_entry_by_id(load_entries(), entry_id)

    context = {
        "entry": entry,
    }

    return render(
        request,
        "menu/menu_detail.html",
        context,
        status=404 if entry is None else 200,
    )
