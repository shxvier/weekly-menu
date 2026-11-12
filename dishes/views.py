"""Страницы блюд: данные получаются через Django ORM."""
from django.shortcuts import get_object_or_404, render

from dishes.models import Dish

# Разрешённые значения параметра sort -> поля модели.
# Произвольный ввод пользователя в order_by() не передаётся.
DISH_SORT_FIELDS = {
    "name": ("name",),
    "calories": ("calories", "name"),
    "-calories": ("-calories", "name"),
}


def parse_positive_int(value):
    """Вернуть положительное целое из строки запроса или None."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def dish_list(request):
    """Список блюд: поиск по названию, лимит калорий, сортировка."""
    raw_limit = request.GET.get("max_calories", "").strip()
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "name")
    max_calories = parse_positive_int(raw_limit)

    dishes = Dish.objects.all()
    if query:
        # Поиск по строковому полю без учёта регистра.
        dishes = dishes.filter(name__icontains=query)
    if max_calories is not None:
        # Фильтрация по одному условию: не больше N ккал.
        dishes = dishes.filter(calories__lte=max_calories)
    dishes = dishes.order_by(*DISH_SORT_FIELDS.get(sort, ("name",)))

    context = {
        "dishes": dishes,
        "max_calories": max_calories,
        "query": query,
        "sort": sort if sort in DISH_SORT_FIELDS else "name",
        "bad_input": bool(raw_limit) and max_calories is None,
    }
    return render(request, "dishes/dish_list.html", context)


def dish_detail(request, dish_id):
    """Карточка блюда и число его появлений в активном меню."""
    dish = get_object_or_404(Dish, pk=dish_id)
    # Обратная связь Dish -> MenuEntry через related_name.
    times_planned = dish.menu_entries.active().count()
    context = {
        "dish": dish,
        "times_planned": times_planned,
    }
    return render(request, "dishes/dish_detail.html", context)
