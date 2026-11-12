"""Страницы меню: данные через Django ORM, ввод – через Django Forms."""
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Max, Min, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from dishes.models import Dish
from menu.forms import MenuEntryForm, MenuFilterForm
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


def status_counts():
    """Число записей всего и по каждому статусу (один запрос)."""
    return MenuEntry.objects.aggregate(
        total_entries=Count("id"),
        active_entries=Count("id", filter=Q(status=MenuEntry.Status.ACTIVE)),
        completed_entries=Count(
            "id", filter=Q(status=MenuEntry.Status.COMPLETED),
        ),
        cancelled_entries=Count(
            "id", filter=Q(status=MenuEntry.Status.CANCELLED),
        ),
    )


def menu_list(request):
    """Записи меню: фильтры (форма MenuFilterForm), сортировка, пагинация."""
    # Если GET-параметров нет, форма не связана с данными (is_bound
    # = False) и ошибок при первом открытии страницы не показывает.
    form = MenuFilterForm(request.GET or None)
    # Форма проверяется один раз; результат используется ниже.
    form_valid = form.is_bound and form.is_valid()
    filters = form.cleaned_data if form_valid else {}
    error = None
    if form.is_bound and not form_valid:
        error = "Проверьте введённые значения фильтров."

    status = filters.get("status", "")
    sort = filters.get("sort") or "date"

    # Исходная выборка – через методы менеджера; по умолчанию – записи
    # меню без отменённых.
    status_filters = {
        MenuEntry.Status.ACTIVE: MenuEntry.objects.active,
        MenuEntry.Status.COMPLETED: MenuEntry.objects.completed,
        MenuEntry.Status.CANCELLED: MenuEntry.objects.cancelled,
    }
    entries = status_filters.get(status, MenuEntry.objects.in_menu)()

    # Фильтры применяются только к проверенным значениям cleaned_data.
    # Для dish и user форма возвращает объекты моделей (или None).
    if filters.get("date"):
        entries = entries.for_date(filters["date"])
    if filters.get("dish"):
        entries = entries.filter(dish_id=filters["dish"].pk)
    if filters.get("user"):
        entries = entries.filter(user_id=filters["user"].pk)
    if filters.get("q"):
        query = filters["q"]
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
            "status",
            "dish_name",
            "calories",
            "user_name",
        )
    )

    # Пагинация применяется после фильтрации и сортировки.
    paginator = Paginator(entries, ENTRIES_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "form": form,
        "entries": page_obj,
        "page_obj": page_obj,
        "counts": status_counts(),
        "status": status,
        "sort": sort,
        "error": error,
    }
    return render(request, "menu/menu_list.html", context)


def creation_initial(params):
    """Начальные значения формы создания записи.

    По умолчанию – сегодняшняя дата. Со страницы «Меню на день» можно
    перейти с готовыми ?dish=, ?user= и ?date=; некорректные значения
    просто не подставляются (проверку всё равно выполнит форма).
    """
    initial = {"menu_date": timezone.localdate()}
    for name in ("dish", "user"):
        value = params.get(name, "")
        if value.isdigit():
            initial[name] = int(value)
    selected_date = parse_date(params.get("date", ""))
    if selected_date and selected_date >= initial["menu_date"]:
        initial["menu_date"] = selected_date
    return initial


def is_dish_taken(cleaned_data, exclude_pk=None):
    """Есть ли блюдо в меню пользователя на эту дату.

    Учитываются записи «Запланировано» и «Выполнено» (in_menu());
    отменённая запись блюдо не занимает. exclude_pk исключает из
    проверки редактируемую запись, чтобы она не мешала самой себе.
    """
    entries = (
        MenuEntry.objects
        .in_menu()
        .for_date(cleaned_data["menu_date"])
        .filter(dish=cleaned_data["dish"], user=cleaned_data["user"])
    )
    if exclude_pk is not None:
        entries = entries.exclude(pk=exclude_pk)
    return entries.exists()


TAKEN_ERROR = "Это блюдо уже есть в меню пользователя на выбранную дату."


def menu_create(request):
    """Создание записи меню: GET – пустая форма, POST – сохранение."""
    if request.method == "POST":
        # Связанная форма: данные из запроса проходят валидацию.
        form = MenuEntryForm(request.POST)
        if form.is_valid():
            if is_dish_taken(form.cleaned_data):
                # Общая ошибка формы, не связанная с одним полем.
                form.add_error(None, TAKEN_ERROR)
            else:
                entry = form.save()
                messages.success(request, "Запись добавлена в меню.")
                return redirect("menu:detail", entry_id=entry.pk)
    else:
        form = MenuEntryForm(initial=creation_initial(request.GET))
    return render(request, "menu/menu_form.html", {"form": form})


def menu_update(request, entry_id):
    """Редактирование записи меню (только со статусом «Запланировано»)."""
    # Отменённую или выполненную запись по прямому адресу изменить
    # нельзя: get_object_or_404() вернёт 404.
    entry = get_object_or_404(MenuEntry.objects.active(), pk=entry_id)
    if request.method == "POST":
        # instance=entry: форма изменяет существующую запись,
        # а не создаёт новую.
        form = MenuEntryForm(request.POST, instance=entry)
        if form.is_valid():
            if is_dish_taken(form.cleaned_data, exclude_pk=entry.pk):
                form.add_error(None, TAKEN_ERROR)
            else:
                form.save()
                messages.success(request, "Изменения сохранены.")
                return redirect("menu:detail", entry_id=entry.pk)
    else:
        form = MenuEntryForm(instance=entry)
    context = {"form": form, "entry_id": entry.pk}
    return render(request, "menu/menu_form.html", context)


@require_POST
def menu_cancel(request, entry_id):
    """Отмена записи меню: статус меняется на «Отменено», запись остаётся.

    Только POST-запрос с CSRF-токеном; GET вернёт 405.
    """
    entry = get_object_or_404(MenuEntry.objects.active(), pk=entry_id)
    entry.cancel()
    messages.success(
        request, f"Запись №{entry.pk} «{entry.dish}» отменена.",
    )
    # Возврат на ту же страницу списка (с фильтрами), если адрес
    # безопасный; иначе – к списку меню.
    next_url = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect("menu:list")


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
        # Несколько условий: пользователь, дата, записи без отменённых.
        day_entries = (
            MenuEntry.objects
            .in_menu()
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

    in_menu = MenuEntry.objects.in_menu()
    # Калорийность по дням: группировка по пользователю и дате.
    calories_by_day = (
        in_menu
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
        "counts": status_counts(),
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
                    filter=Q(
                        menu_entries__status__in=MenuEntry.IN_MENU_STATUSES,
                    ),
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
            .filter(menu_entries__status__in=MenuEntry.IN_MENU_STATUSES)
            .annotate(times_planned=Count("menu_entries"))
            .filter(times_planned__gt=threshold)
            .values("times_planned", dish_name=F("name"))
            .order_by("-times_planned", "dish_name")
        ),
        "threshold": threshold,
    }
    return render(request, "menu/statistics.html", context)
