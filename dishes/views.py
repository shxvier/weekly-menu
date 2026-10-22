from datetime import date

from django.http import HttpResponse

from homepage.views import page
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
    items = ""
    for dish in load_dishes(DISHES_FILE):
        text = f"{dish.name} – {dish.calories} ккал ({dish.dish_type})"
        link = f'<a href="/dishes/{dish.id}/">{text}</a>'
        items += f'<li class="list-group-item">{link}</li>'
    content = f"""
    <h1>Блюда</h1>
    <ul class="list-group">{items}</ul>
    """
    return HttpResponse(page("Меню на неделю – блюда", content))


def dish_detail(request, dish_id):
    dishes = load_dishes(DISHES_FILE)
    dish = find_dish_by_id(dishes, dish_id)
    if dish is None:
        content = """
        <h1 class="text-danger">Блюдо не найдено</h1>
        <a href="/dishes/" class="btn btn-outline-secondary">
            ← к списку блюд
        </a>
        """
        return HttpResponse(page("Блюдо не найдено", content), status=404)
    users = load_users(USERS_FILE)
    entries = load_menu(MENU_FILE, dishes, users)
    planned = is_dish_planned(entries, dish, date.today().isoformat())
    status = "в меню" if planned else "не в меню"
    badge = "bg-success" if planned else "bg-secondary"
    content = f"""
    <div class="card">
        <div class="card-body">
            <h5 class="card-title">{dish.name}</h5>
            <p class="card-text"><strong>ID:</strong> {dish.id}</p>
            <p class="card-text">
                <strong>Калорийность:</strong> {dish.calories} ккал
            </p>
            <p class="card-text"><strong>Тип:</strong> {dish.dish_type}</p>
            <p class="card-text">
                Статус на сегодня:
                <span class="badge {badge}">{status}</span>
            </p>
            <a href="/dishes/" class="btn btn-outline-secondary">
                ← к списку блюд
            </a>
        </div>
    </div>
    """
    return HttpResponse(page(dish.name, content), status=200)
