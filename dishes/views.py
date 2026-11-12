"""Страницы блюд: данные через Django ORM, ввод – через Django Forms."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from dishes.forms import DishForm
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


def dish_detail(request, slug):
    """Карточка блюда (поиск по slug) и число его появлений в меню."""
    dish = get_object_or_404(Dish, slug=slug)
    # Обратная связь Dish -> MenuEntry через related_name.
    times_planned = dish.menu_entries.in_menu().count()
    context = {
        "dish": dish,
        "times_planned": times_planned,
    }
    return render(request, "dishes/dish_detail.html", context)


def dish_create(request):
    """Новое блюдо; файл фотографии приходит в request.FILES."""
    if request.method == "POST":
        # Обычные поля – из request.POST, загруженный файл –
        # из request.FILES.
        form = DishForm(request.POST, request.FILES)
        if form.is_valid():
            dish = form.save()
            messages.success(request, "Блюдо добавлено.")
            return redirect(dish)
    else:
        form = DishForm()
    return render(request, "dishes/dish_form.html", {"form": form})


def dish_update(request, slug):
    """Редактирование блюда, замена или удаление фотографии."""
    dish = get_object_or_404(Dish, slug=slug)
    # Название для заголовка запоминаем до валидации: is_valid()
    # переносит введённые значения в объект dish.
    dish_name = dish.name
    if request.method == "POST":
        form = DishForm(request.POST, request.FILES, instance=dish)
        if form.is_valid():
            form.save()
            messages.success(request, "Изменения сохранены.")
            # redirect() с объектом использует get_absolute_url().
            return redirect(dish)
    else:
        form = DishForm(instance=dish)
    return render(
        request,
        "dishes/dish_form.html",
        {"form": form, "dish": dish, "dish_name": dish_name},
    )
