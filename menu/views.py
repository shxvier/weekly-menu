"""Страницы меню: данные получаются через Django ORM."""
from datetime import datetime

from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Max, Min, Q, Sum
from django.shortcuts import get_object_or_404, render

from dishes.models import Dish
from menu.models import MenuEntry
from users.models import User
from utils import parse_date

# Записей меню на одной странице списка.
ENTRIES_PER_PAGE = 5

# Разрешённые значения параметра sort -> поля сортировки.
# Второе поле id обеспечивает стабильный порядок при равных значениях.
ENTRY_SORT_FIELDS = {
    "date": ("menu_date", "id"),
    "dish": ("dish__name", "menu_date", "id"),
    "user": ("user__name", "menu_date", "id"),
    "calories": ("-dish__calories", "menu_date", "id"),
}


def menu_list(request):
    """Активные записи меню: фильтры, поиск, сортировка, пагинация."""
    raw_date = request.GET.get("date", "").strip()
    dish_id = request.GET.get("dish", "").strip()
    user_id = request.GET.get("user", "").strip()
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "date")
    if sort not in ENTRY_SORT_FIELDS:
        sort = "date"
    error = None

    # Только активные записи меню (метод менеджера).
    entries = MenuEntry.objects.active()

    if raw_date:
        try:
            selected_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            error = "Укажите корректную дату."
        else:
            entries = entries.for_date(selected_date)
    # Фильтрация по внешним ключам.
    if dish_id.isdigit():
        entries = entries.filter(dish_id=int(dish_id))
    if user_id.isdigit():
        entries = entries.filter(user_id=int(user_id))
    if query:
        # Поиск по нескольким полям связанных моделей.
        entries = entries.filter(
            Q(dish__name__icontains=query) | Q(user__name__icontains=query)
        )

    # Поля связанных моделей под привычными для шаблона именами.
    entries = (
        entries
        .annotate(
            dish_name=F("dish__name"),
            calories=F("dish__calories"),
            user_name=F("user__name"),
        )
        .order_by(*ENTRY_SORT_FIELDS[sort])
        .values(
            "id",
            "menu_date",
            "is_cancelled",
            "dish_name",
            "calories",
            "user_name",
        )
    )

    # Пагинация применяется после фильтрации и сортировки.
    paginator = Paginator(entries, ENTRIES_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "entries": page_obj,
        "page_obj": page_obj,
        "counts": MenuEntry.objects.aggregate(
            active_entries=Count("id", filter=Q(is_cancelled=False)),
            cancelled_entries=Count("id", filter=Q(is_cancelled=True)),
        ),
        "dishes": Dish.objects.order_by("name"),
        "users": User.objects.order_by("name"),
        "date_value": raw_date,
        "selected_dish": dish_id,
        "selected_user": user_id,
        "query": query,
        "sort": sort,
        "error": error,
    }
    return render(request, "menu/menu_list.html", context)


def menu_detail(request, entry_id):
    """Запись меню вместе с блюдом и пользователем (один SQL-запрос)."""
    entry = get_object_or_404(
        MenuEntry.objects.select_related("dish", "user"),
        pk=entry_id,
    )
    return render(request, "menu/menu_detail.html", {"entry": entry})


def day_menu(request):
    """Меню пользователя на дату: ?user=<id>&date=ГГГГ-ММ-ДД."""
    raw_date = request.GET.get("date", "").strip()
    raw_user = request.GET.get("user", "").strip()
    menu_date = parse_date(raw_date) if raw_date else None
    user = None
    if raw_user.isdigit():
        user = User.objects.filter(pk=int(raw_user)).first()

    context = {
        "users": User.objects.order_by("name"),
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
        # Несколько условий: пользователь, дата, только активные записи.
        day_entries = (
            MenuEntry.objects
            .active()
            .for_date(menu_date)
            .filter(user=user)
            .select_related("dish")
            .order_by("dish__calories")
        )
        day_calories = (
            day_entries.aggregate(total=Sum("dish__calories"))["total"]
            or 0
        )
        # Блюда, которых ещё нет в меню на этот день.
        free_dishes = Dish.objects.exclude(
            pk__in=day_entries.values_list("dish_id", flat=True),
        ).order_by("name")
        context.update({
            "searched": True,
            "entries": day_entries,
            "free_dishes": free_dishes,
            "day_calories": day_calories,
            "left_calories": user.daily_limit - day_calories,
            "excess_calories": day_calories - user.daily_limit,
        })
    return render(request, "menu/day_menu.html", context)


def statistics(request):
    """Статистика по меню и блюдам: агрегирование и группировка."""
    raw_threshold = request.GET.get("min_count", "2")
    threshold = int(raw_threshold) if raw_threshold.isdigit() else 2

    active = MenuEntry.objects.active()
    # Калорийность по дням: группировка по пользователю и дате.
    calories_by_day = (
        active
        .values(
            "menu_date",
            user_name=F("user__name"),
            daily_limit=F("user__daily_limit"),
        )
        .annotate(
            dishes_count=Count("id"),
            day_calories=Sum("dish__calories"),
        )
    )

    context = {
        "counts": MenuEntry.objects.aggregate(
            total_entries=Count("id"),
            active_entries=Count("id", filter=Q(is_cancelled=False)),
            cancelled_entries=Count("id", filter=Q(is_cancelled=True)),
        ),
        "calories_range": Dish.objects.aggregate(
            dishes_count=Count("id"),
            min_calories=Min("calories"),
            max_calories=Max("calories"),
            avg_calories=Avg("calories"),
        ),
        "dish_types": (
            Dish.objects
            .values("dish_type")
            .annotate(
                dishes_count=Count("id"),
                avg_calories=Avg("calories"),
            )
            .order_by("-dishes_count", "dish_type")
        ),
        # Блюда без записей тоже попадают в результат (счётчик 0):
        # подсчёт идёт от модели Dish с условием внутри Count().
        "popularity": (
            Dish.objects
            .annotate(
                dish_name=F("name"),
                times_planned=Count(
                    "menu_entries",
                    filter=Q(menu_entries__is_cancelled=False),
                ),
            )
            .values("dish_name", "times_planned")
            .order_by("-times_planned", "dish_name")
        ),
        "calories_by_day": calories_by_day.order_by("menu_date", "user_name"),
        # Условие на агрегат -> HAVING: дни сверх лимита пользователя.
        "over_limit": (
            calories_by_day
            .filter(day_calories__gt=F("daily_limit"))
            .annotate(excess=F("day_calories") - F("daily_limit"))
            .order_by("-excess")
        ),
        "frequent": (
            Dish.objects
            .filter(menu_entries__is_cancelled=False)
            .annotate(times_planned=Count("menu_entries"))
            .filter(times_planned__gt=threshold)
            .values("times_planned", dish_name=F("name"))
            .order_by("-times_planned", "dish_name")
        ),
        "threshold": threshold,
    }
    return render(request, "menu/statistics.html", context)
