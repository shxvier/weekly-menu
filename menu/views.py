from django.http import HttpResponse

from homepage.views import page
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
    items = ""
    for entry in load_entries():
        status = "отменено" if entry.is_cancelled else "активно"
        badge = "bg-secondary" if entry.is_cancelled else "bg-success"
        items += f"""
        <li class="list-group-item d-flex justify-content-between">
            <a href="/menu/{entry.id}/">
                {entry.menu_date} – {entry.dish.name} ({entry.user.name})
            </a>
            <span class="badge {badge}">{status}</span>
        </li>
        """
    content = f"""
    <h1>Меню</h1>
    <ul class="list-group">{items}</ul>
    """
    return HttpResponse(page("Меню на неделю – меню", content))


def menu_detail(request, entry_id):
    entry = find_entry_by_id(load_entries(), entry_id)
    if entry is None:
        content = """
        <h1 class="text-danger">Запись меню не найдена</h1>
        <a href="/menu/" class="btn btn-outline-secondary">
            ← к списку меню
        </a>
        """
        return HttpResponse(
            page("Запись меню не найдена", content),
            status=404,
        )
    status = "отменено" if entry.is_cancelled else "активно"
    badge = "bg-secondary" if entry.is_cancelled else "bg-success"
    content = f"""
    <div class="card">
        <div class="card-body">
            <h5 class="card-title">Запись меню №{entry.id}</h5>
            <p class="card-text">Блюдо: {entry.dish.name}</p>
            <p class="card-text">Дата: {entry.menu_date}</p>
            <p class="card-text">Пользователь: {entry.user.name}</p>
            <p class="card-text">
                Статус: <span class="badge {badge}">{status}</span>
            </p>
            <a href="/menu/" class="btn btn-outline-secondary">
                ← к списку меню
            </a>
        </div>
    </div>
    """
    return HttpResponse(page(f"Запись меню №{entry.id}", content))
