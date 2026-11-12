# Сервис формирования меню на неделю

Приложение для составления меню на неделю: подбор блюд по дням,
учёт калорийности и сохранение меню. Состоит из консольной версии
(`main.py`) и веб-интерфейса на Django.

## Возможности

- просмотр и поиск блюд, отбор по калорийности и сортировка;
- добавление и редактирование блюд (с фотографией) через веб-формы;
- добавление новых пользователей;
- добавление блюда в меню пользователя на выбранный день и
  редактирование записи (одно блюдо нельзя добавить в один день дважды,
  прошедшую дату выбрать нельзя);
- проверка калорийности дня относительно лимита пользователя;
- проверка заполненности дней недели;
- отмена блюда в меню (запись остаётся в истории со статусом
  «отменено» и больше не учитывается);
- сохранение и загрузка данных в JSON.

## Объектная модель

| Класс | Атрибуты | Методы |
|-------|----------|--------|
| `Dish` | `id`, `name`, `calories`, `dish_type` | `fits_limit()`, `validate_calories()` (static), `from_data()` (classmethod), `__str__()` |
| `User` | `id`, `name`, `goal`, `daily_limit` | `from_data()` (classmethod), `__str__()` |
| `MenuEntry` | `id`, `dish`, `menu_date`, `user`, `is_cancelled` | `cancel()`, `__str__()` |

Взаимодействие объектов: запись меню `MenuEntry` хранит ссылки на
объекты `Dish` и `User` (`entry.dish.name`, `entry.user.daily_limit`),
а не их идентификаторы. Коллекции приложения: `List[Dish]`,
`List[User]`, `List[MenuEntry]`.

Операции над коллекциями остаются обычными функциями модулей
`models/dishes.py`, `models/users.py`, `models/menu.py`; загрузка и
сохранение — функциями `storage.py`. В JSON сохраняются только данные:
у записи меню — `dish_id` и `user_id`; при загрузке по ним
восстанавливаются ссылки на объекты.

## Веб-интерфейс (Django)

Используется фреймворк Django 5.2. С ПР9 веб-слой получает данные через
Django ORM из базы Django `db.sqlite3` (модели в `models.py` приложений,
структура базы управляется миграциями). Страницы строятся
системой шаблонов Django (DTL): представления только готовят данные
и передают их в шаблон через `render(request, шаблон, context)`.
Функция `page()` из ПР5 удалена — HTML в Python больше не собирается.

Django-проект — `weeklymenu/`, приложения:

- `homepage` — главная страница и страница ошибки 404;
- `dishes` — страницы блюд;
- `menu` — страницы записей меню;
- `users` — модель пользователя (страниц нет).

| URL | View | Страница |
|-----|------|----------|
| `/` | `homepage.views.index` | главная, навигация |
| `/dishes/` | `dishes.views.dish_list` | список блюд: поиск по названию, лимит калорий, сортировка |
| `/dishes/<slug>/` | `dishes.views.dish_detail` | карточка блюда по slug (например `/dishes/grecheskii-salat-3/`), сколько раз оно в меню |
| `/menu/` | `menu.views.menu_list` | записи меню: фильтр по дате, блюду, пользователю, статусу, поиск, сортировка, пагинация |
| `/dishes/create/` | `dishes.views.dish_create` | новое блюдо с фотографией (ПР11) |
| `/dishes/<slug>/edit/` | `dishes.views.dish_update` | редактирование блюда, замена фотографии (ПР11) |
| `/admin/` | Django Admin | административная панель |
| `/menu/create/` | `menu.views.menu_create` | новая запись меню (ПР11) |
| `/menu/<id>/` | `menu.views.menu_detail` | карточка записи меню |
| `/menu/<id>/edit/` | `menu.views.menu_update` | редактирование запланированной записи (ПР11) |
| `/menu/<id>/cancel/` | `menu.views.menu_cancel` | отмена записи, только POST (ПР11) |
| `/menu/day/?user=<id>&date=<дата>` | `menu.views.day_menu` | меню пользователя на день, калорийность, блюда, которые можно добавить |
| `/menu/statistics/` | `menu.views.statistics` | статистика по меню и блюдам |

Параметры списка меню: `?date=ГГГГ-ММ-ДД&dish=<id>&user=<id>&status=active|completed|cancelled&q=<текст>&sort=date|dish|user|calories&page=<N>`
(по 5 записей на страницу). Параметры списка блюд:
`?q=<текст>&max_calories=<N>&sort=name|calories|-calories`.

### Шаблоны

- `templates/base.html` — базовый шаблон: `<head>`, Bootstrap 5.3,
  собственный CSS, логотип, навигация, подвал, JS; блоки
  `{% block title %}` и `{% block content %}`;
- `templates/includes/navigation.html` — меню (подключается через
  `{% include %}`);
- `homepage/templates/homepage/index.html`, `404.html`;
- `dishes/templates/dishes/dish_list.html`, `dish_detail.html`,
  `includes/dish_card.html` — карточка блюда;
- `menu/templates/menu/menu_list.html`, `menu_detail.html`,
  `includes/menu_status.html` — статус записи меню.

Все дочерние шаблоны используют `{% extends "base.html" %}`. В шаблонах
применяются циклы `{% for %}` с `{% empty %}`, условия `{% if %}`
(отменённая/активная запись, найден ли объект), фильтры `length`,
`default`, `capfirst`. Ссылки строятся только через именованные
маршруты с пространствами имён: `{% url 'dishes:detail' dish.id %}`,
`{% url 'menu:list' %}`, `{% url 'homepage:index' %}`.

### Статические файлы

`homepage/static/homepage/`: `css/style.css` (собственные стили
карточек, статусов и шапки), `js/main.js` (подставляет текущий год в
подвал), `img/logo.png`. Подключаются через `{% load static %}` и
`{% static '...' %}`.

Для несуществующих `id` страницы возвращают код 404, для любых
неизвестных адресов подключён собственный обработчик `handler404`
(виден при `DEBUG = False`).

Запуск веб-сервера:

```
pip install -r requirements.txt
python -m db.import_json
python manage.py migrate
python manage.py runserver
```

После этого сайт доступен по адресу http://127.0.0.1:8000/.

## Модели данных и Django ORM (ПР9)

| Модель | Приложение | Поля | Связи |
|--------|------------|------|-------|
| `Dish` — блюдо | `dishes/models.py` | `name` (CharField 200), `slug` (SlugField, уникальный, формируется автоматически), `calories` (PositiveIntegerField ≥ 1, `help_text`), `dish_type` (CharField с choices, по умолчанию «обед»), `is_light` (GeneratedField: `calories <= 300`) | — |
| `User` — пользователь | `users/models.py` | `name` (CharField 100), `goal` (CharField 200, `blank=True`), `daily_limit` (PositiveIntegerField ≥ 1) | — |
| `MenuEntry` — запись меню | `menu/models.py` | `dish`, `user` (ForeignKey), `menu_date` (DateField), `status` (TextChoices: `active` «Запланировано», `completed` «Выполнено», `cancelled` «Отменено»; по умолчанию `active`) | `dish` → `Dish`, `user` → `User`; `on_delete=PROTECT`, `related_name="menu_entries"` |

Первичные ключи `id` Django создаёт автоматически (`BigAutoField`).
`PROTECT` запрещает удалить блюдо или пользователя, пока на них
ссылаются записи меню, — история меню сохраняется. Обратные связи:
`dish.menu_entries.all()`, `user.menu_entries.all()`. Метод
`MenuEntry.cancel()` переводит запись в статус «Отменено»
(`save(update_fields=["status"])`). До ПР10 вместо `status` было поле
`is_cancelled`; его значения перенесены миграцией данных
`menu/migrations/0003_migrate_menu_statuses.py`, после чего поле удалено.
Модель `users.User` — пользователь предметной области, а не встроенная
модель аутентификации Django.

### Миграции и перенос данных из базы ПР7

Стратегия: таблицы создаются миграциями Django в базе `db.sqlite3`,
база ПР7 `data/weekly_menu.sqlite` остаётся неизменным источником, и
данные переносятся в новые таблицы с сохранением идентификаторов.

```
python manage.py migrate                 # создать таблицы
python db/inspect_source_db.py           # структура и число записей в базе ПР7
python db/import_sqlite_to_orm.py        # перенос: блюда, пользователи, записи меню
```

Скрипт переноса работает в одной транзакции (`transaction.atomic()`),
использует `update_or_create(pk=...)` (повторный запуск не создаёт
дублей), переводит строки дат в `date`, а `0/1` — в `bool`. Переносятся
9 блюд, 2 пользователя и 17 записей меню. Если базы ПР7 нет, её можно
собрать из JSON: `python -m db.import_json`.

### ORM-запросы проекта

| № | Где | Выражение | Вид |
|---|-----|-----------|-----|
| 1 | список блюд | `Dish.objects.all()` | получение набора |
| 2 | список блюд | `.filter(name__icontains=q)` | поиск по строковому полю |
| 3 | список блюд | `.filter(calories__lte=N)` | фильтр по одному условию |
| 4 | список блюд | `.order_by(*DISH_SORT_FIELDS[sort])` | сортировка по одному и нескольким полям |
| 5 | карточка блюда | `get_object_or_404(Dish, slug=slug)` (в ПР9 — по `pk`) | один объект, 404 |
| 6 | карточка блюда | `dish.menu_entries.in_menu().count()` | обратная связь, метод менеджера, подсчёт |
| 7 | список меню | `MenuEntry.objects.in_menu()` (или `active()`/`completed()`/`cancelled()` по параметру status) + `.for_date(...)`, `.filter(dish_id=...)`, `.filter(user_id=...)` | фильтр по нескольким условиям и внешним ключам |
| 8 | список меню | `.filter(Q(dish__name__icontains=q) \| Q(user__name__icontains=q))` | поиск по нескольким полям связанных моделей |
| 9 | список меню | `.annotate(dish_name=F("dish__name"), ...).order_by(...).values(...)` | поля связанных моделей, сортировка по связанному полю, сокращённый набор полей |
| 10 | список меню | `Paginator(entries, 5).get_page(page)` | постраничный вывод |
| 11 | список меню, статистика | `MenuEntry.objects.aggregate(Count("id", filter=Q(status=...)))` по каждому статусу | сводный показатель |
| 12 | запись меню | `get_object_or_404(MenuEntry.objects.select_related("dish", "user"), pk=...)` | связанные объекты одним запросом |
| 13 | меню на день | `MenuEntry.objects.in_menu().for_date(d).filter(user=user).select_related("dish")` | несколько условий, `select_related` |
| 14 | меню на день | `day_entries.aggregate(total=Sum("dish__calories"))` | сумма по связанному полю |
| 15 | меню на день | `Dish.objects.exclude(pk__in=day_entries.values_list("dish_id", flat=True))` | исключение `exclude()` |
| 16 | статистика | `Dish.objects.aggregate(Count, Min, Max, Avg)` | агрегирование |
| 17 | статистика | `Dish.objects.values("dish_type").annotate(Count, Avg)` | группировка |
| 18 | статистика | `Dish.objects.annotate(times_planned=Count("menu_entries", filter=Q(menu_entries__status__in=...)))` | аннотирование, блюда без записей сохраняются (0) |
| 19 | статистика | `active.values("menu_date", user_name=F(...)).annotate(Count, Sum)` | группировка по пользователю и дате |
| 20 | статистика | `.filter(day_calories__gt=F("daily_limit")).annotate(excess=...)` | условие на агрегат (HAVING) |
| 21 | статистика | `Dish.objects.filter(menu_entries__status__in=...).annotate(Count).filter(times_planned__gt=N)` | фильтр по связанной модели + HAVING |

Поле сортировки выбирается только из словарей `DISH_SORT_FIELDS` и
`ENTRY_SORT_FIELDS`, неизвестное значение заменяется сортировкой по
умолчанию — пользовательский ввод не передаётся в `order_by()`.
Отменённые записи не учитываются ни в списке (по умолчанию), ни в меню
на день, ни в статистике.

Поиск по кириллице. Встроенный `LIKE` SQLite не учитывает регистр только
для латиницы, поэтому `homepage/sqlite_unicode.py` при подключении к базе
регистрирует Unicode-версию функции `like()` (сигнал `connection_created`).
Код запросов остаётся стандартным: `name__icontains="овс"` находит
«Овсяная каша».

## Административная панель и дополнительные возможности (ПР10)

Вход: `/admin/` под суперпользователем Django
(`python manage.py createsuperuser`). Суперпользователь — учётная запись
`django.contrib.auth`, а не объект `users.User`.

| Модель | Настройки `ModelAdmin` |
|--------|------------------------|
| `Dish` (`dishes/admin.py`) | столбцы id, название, ккал, тип, «лёгкое», «записей в меню» (аннотация `Count` в `get_queryset`), ссылка на сайт; переход по названию; `list_editable` для ккал; поиск по названию; фильтры по типу и `is_light`; сортировка по названию; 20 на странице; `readonly_fields` id, slug, is_light; inline записей меню; `view_on_site` |
| `User` (`users/admin.py`) | id, имя, цель, лимит; поиск по имени и цели; inline записей меню |
| `MenuEntry` (`menu/admin.py`) | id, дата, блюдо, ккал блюда (`@admin.display`, сортировка по `dish__calories`), пользователь, статус; поиск по `dish__name`, `user__name`; фильтры по дате, статусу, типу блюда, пользователю; `list_select_related`; `date_hierarchy`; `autocomplete_fields`; массовые действия «Отменить», «Отметить как выполненные», «Вернуть в запланированные» |

Названия приложений на русском заданы в `apps.py` (`verbose_name`),
моделей и полей — в `Meta` и `verbose_name` полей.

Менеджер записей меню (`menu/models.py`):
`MenuEntry.objects.active()`, `.completed()`, `.cancelled()`,
`.in_menu()` (все, кроме отменённых), `.for_date(date)`. Методы
используются в представлениях списка, меню на день, карточки блюда и
статистики.

Правило предметной области: в меню дня (калорийность, запрет повторного
блюда на дату, статистика) учитываются записи «Запланировано» и
«Выполнено». Отменённая запись остаётся в истории, но блюдо снова можно
добавить. В отличие от бронирования, где завершённая бронь уже в прошлом,
съеденное блюдо остаётся частью рациона дня.

Дополнительно:

- `Dish.is_light` — `GeneratedField` (`db_persist=True`): база данных
  сама вычисляет признак «до 300 ккал» и пересчитывает его при
  изменении калорийности;
- `Dish.slug` — транслитерация названия (`Unidecode`) + id, формируется
  в `save()`, уникален; заполнен у существующих блюд миграцией
  `dishes/migrations/0005_populate_dish_slugs.py`;
  `Dish.get_absolute_url()` строит адрес через `reverse("dishes:detail")`
  и используется в шаблонах и в админке («Смотреть на сайте»);
- контекстный процессор `dishes/context_processors.py` передаёт во все
  шаблоны `site_name`, `dishes_count` (в навигации «Блюда (N)») и
  константы статусов `MenuStatus`;
- Django Debug Toolbar (при `DEBUG = True`, `INTERNAL_IPS`) — вкладка SQL.
  Число запросов на страницах не зависит от числа записей: карточка
  записи меню — 1 запрос с JOIN двух таблиц, список меню — 5 (подсчёт
  для пагинатора, счётчики статусов, два справочника, текущая страница),
  плюс 1 запрос контекстного процессора.

## Формы Django (ПР11)

| Форма | Тип | Где используется |
|-------|-----|------------------|
| `MenuFilterForm` (`menu/forms.py`) | `forms.Form` | фильтры списка меню `/menu/` (GET): `date` — `DateField`, `dish` и `user` — `ModelChoiceField`, `status` и `sort` — `ChoiceField`, `q` — `CharField` |
| `MenuEntryForm` (`menu/forms.py`) | `ModelForm` (`dish`, `menu_date`, `user`) | создание и редактирование записи меню; поле `status` в форму не входит |
| `DishForm` (`dishes/forms.py`) | `ModelForm` (`name`, `calories`, `dish_type`, `image`) | создание и редактирование блюда с загрузкой фотографии |

Список меню создаёт форму как `MenuFilterForm(request.GET or None)`:
без параметров форма не связана с данными и ошибок не показывает. Фильтры
применяются только к проверенным значениям `cleaned_data` (для блюда и
пользователя — объекты моделей). При некорректных параметрах
(`?dish=999`, `?sort=id;DROP`, `?date=2026-13-40`, `?q=г`) страница
открывается без ошибки 500: поля показывают сообщения, над списком —
«Проверьте введённые значения фильтров.», выводится список без фильтров.
Сортировка, пагинация и сохранение фильтров в ссылках `{% querystring %}`
работают как в ПР9.

Валидация:

| Где | Проверка |
|-----|----------|
| встроенная | тип даты, существование блюда/пользователя в `queryset`, допустимые значения `ChoiceField`, обязательные поля `ModelForm`, `MinValueValidator(1)` у калорийности, `ImageField` проверяет, что файл — изображение |
| `dishes/validators.py` | `validate_image_size()` — фото не больше 2 МБ (подключён к полю `Dish.image`) |
| `MenuFilterForm.clean_q()` | строка поиска без лишних пробелов, не короче 2 символов |
| `MenuEntryForm.clean_menu_date()` | нельзя выбрать прошедшую дату (при редактировании прежнюю дату записи можно оставить) |
| `MenuEntryForm.clean()` | калорийность блюда не больше дневного лимита пользователя (два поля сразу) |
| `DishForm.clean_name()` | название без повторов (без учёта регистра и лишних пробелов) |
| представления `menu_create` / `menu_update` | блюдо не повторяется в меню пользователя на дату: `MenuEntry.objects.in_menu()...exists()`, при редактировании `.exclude(pk=entry.pk)`; ошибка формы `form.add_error(None, ...)` |

Отменённая запись блюдо не занимает, «Запланировано» и «Выполнено» —
занимают (правило ПР10).

Создание (`/menu/create/`): GET — пустая форма с сегодняшней датой
(`initial`); со страницы «Меню на день» кнопка «Добавить в меню»
подставляет блюдо, пользователя и дату. POST — проверка, `form.save()`,
перенаправление на карточку записи и сообщение `django.contrib.messages`.
Редактирование (`/menu/<id>/edit/`): `MenuEntryForm(instance=entry)`,
доступно только для записей «Запланировано»
(`get_object_or_404(MenuEntry.objects.active(), pk=...)`), отменённые и
несуществующие — 404. Создание и редактирование используют один шаблон
`menu/menu_form.html`.

Отмена (`/menu/<id>/cancel/`): `@require_POST`, кнопка — POST-форма с
`{% csrf_token %}`; вызывается `entry.cancel()`, запись остаётся в базе
со статусом «Отменено». GET-запрос — 405, повторная отмена — 404, после
отмены возврат на ту же страницу списка (адрес `next` проверяется
`url_has_allowed_host_and_scheme`).

Шаблоны выводят поля по отдельности (`templates/includes/form_field.html`:
`label_tag`, поле, `help_text`, ошибки поля), общие ошибки —
`form.non_field_errors`. Виджеты задают классы Bootstrap (`form-control`,
`form-select`) и `type="date"`.

Фотографии блюд: `Dish.image` — `ImageField(upload_to="dishes/")`
(нужен Pillow), `MEDIA_URL = "/media/"`, `MEDIA_ROOT = BASE_DIR / "media"`,
при `DEBUG` файлы раздаёт `static()` в `weeklymenu/urls.py`. Форма блюда
отправляется с `enctype="multipart/form-data"`, представление передаёт в
форму `request.POST` и `request.FILES`. Фото выводится в карточке и
списке блюд (`dish.image.url`), без фото — «Фотография не загружена.».
Загрузить и заменить фото можно и в админке (поле «Фотография»,
превью). Каталог `media/` в Git не хранится.

## База данных (SQLite, ПР7)

Файл базы — `data/weekly_menu.sqlite`. С ПР9 это исходная база для
переноса в Django ORM; веб-приложение с ней больше не работает. Файлы
`sql/` и `db/database.py` сохранены как реализация ПР7 (на них
продолжают работать тесты SQL-слоя). JSON-файлы — данные консольной
версии и источник для `db/import_json.py`.

### Таблицы

`dishes` — блюда

| Поле | Тип | Назначение |
|------|-----|------------|
| `id` | INTEGER, PRIMARY KEY | идентификатор |
| `name` | TEXT, NOT NULL | название |
| `calories` | INTEGER, NOT NULL, > 0 | калорийность |
| `dish_type` | TEXT, NOT NULL | завтрак / обед / ужин / перекус |

`users` — пользователи

| Поле | Тип | Назначение |
|------|-----|------------|
| `id` | INTEGER, PRIMARY KEY | идентификатор |
| `name` | TEXT, NOT NULL | имя |
| `goal` | TEXT, допускает NULL | цель |
| `daily_limit` | INTEGER, NOT NULL, > 0 | лимит ккал в день |

`menu_entries` — записи меню

| Поле | Тип | Назначение |
|------|-----|------------|
| `id` | INTEGER, PRIMARY KEY | идентификатор |
| `dish_id` | INTEGER, NOT NULL, FOREIGN KEY → `dishes.id` | блюдо |
| `user_id` | INTEGER, NOT NULL, FOREIGN KEY → `users.id` | пользователь |
| `menu_date` | TEXT, NOT NULL | дата ГГГГ-ММ-ДД |
| `is_cancelled` | INTEGER, 0/1, DEFAULT 0 | признак отмены |

Связи: у блюда и у пользователя может быть много записей меню; каждая
запись относится ровно к одному блюду и одному пользователю.

### Файлы

- `sql/schema.sql` — `CREATE TABLE IF NOT EXISTS` для трёх таблиц;
- `sql/queries.sql` — 18 проверенных запросов с комментариями:
  выборка списков, `WHERE` (в т.ч. `IN`, `BETWEEN`, подзапрос
  `NOT IN`), `JOIN` / `LEFT JOIN`, агрегаты (`COUNT`, `SUM`, `MIN`,
  `MAX`, `AVG`), `GROUP BY`, `HAVING`;
- `db/database.py` — `get_connection()` (включает
  `PRAGMA foreign_keys = ON` и `row_factory = sqlite3.Row`),
  `fetch_all()` / `fetch_one()` для параметризованных запросов;
- `db/import_json.py` — перенос данных из JSON (`executemany`,
  параметры `?`, `commit` / `rollback`); создаёт схему и перед
  вставкой очищает таблицы, поэтому запуск можно повторять.

Создание и заполнение базы:

```
python -m db.import_json
```

В ПР7 представления выполняли эти запросы через `sqlite3`; в ПР9 они
заменены ORM-выражениями (см. таблицу выше).

## Структура проекта

- `manage.py` — управление Django-проектом;
- `weeklymenu/` — настройки и корневые маршруты Django;
- `homepage/` — главная, 404, Unicode-`LIKE` для SQLite, общая статика;
- `dishes/` — модель `Dish`, форма `DishForm`, валидатор фото, админка,
  контекстный процессор, представления и шаблоны блюд;
- `menu/` — модель `MenuEntry` и её менеджер, формы `MenuFilterForm` и
  `MenuEntryForm`, админка, представления и шаблоны меню;
- `users/` — модель `User` и её админка;
- `*/migrations/` — миграции моделей (хранятся в Git);
- `templates/` — общие шаблоны проекта;
- `db/` — скрипты: `import_json.py` (JSON → база ПР7),
  `inspect_source_db.py`, `import_sqlite_to_orm.py` (база ПР7 → ORM),
  `database.py` (подключение `sqlite3`, ПР7);
- `sql/` — схема и SQL-запросы ПР7;
- `main.py`, `models/`, `storage.py`, `utils.py` — консольная версия
  (ПР2–ПР3, данные в JSON);
- `data/` — JSON-файлы и исходная база ПР7 `weekly_menu.sqlite`;
- `tests/` — автоматизированные тесты (pytest, pytest-django).

Локальная база Django `db.sqlite3` и загруженные файлы `media/` в
репозиторий не входят (`.gitignore`): после клонирования она создаётся миграциями и
заполняется скриптом переноса.

## Требования

- Python 3.x, Django 5.2, django-debug-toolbar, Unidecode, Pillow;
- pytest, pytest-django;
- flake8.

## Запуск веб-приложения

```
git clone https://github.com/shxvier/weekly-menu
cd weekly-menu
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python db/import_sqlite_to_orm.py
python manage.py createsuperuser
python manage.py runserver
```

Сайт: http://127.0.0.1:8000/, административная панель: http://127.0.0.1:8000/admin/.

## Запуск консольной версии

```
python main.py
```

## Проверки

```
python manage.py check
python manage.py showmigrations
python manage.py makemigrations --check
pytest -v
flake8 . --extend-exclude=venv
```

## Текущий этап разработки

ПР9: слой данных переведён на Django ORM (модели, миграции, перенос из
базы ПР7, фильтрация, поиск, сортировка, пагинация).

ПР10: настроена административная панель, добавлены менеджер записей
меню, статусы TextChoices вместо `is_cancelled`, вычисляемое поле
`is_light`, адреса блюд по slug и `get_absolute_url()`, контекстный
процессор и Django Debug Toolbar.

ПР11: ввод данных переведён на Django Forms — форма фильтрации списка
меню, создание, редактирование и отмена записей меню, создание и
редактирование блюд с загрузкой фотографии.

## Автор

Журавлев Алексей Игоревич, ЭФБО-12-24.
