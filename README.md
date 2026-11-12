# Сервис формирования меню на неделю

Приложение для составления меню на неделю: подбор блюд по дням,
учёт калорийности и сохранение меню. Состоит из консольной версии
(`main.py`) и веб-интерфейса на Django.

## Возможности

- просмотр и поиск блюд, отбор по калорийности и сортировка;
- добавление новых блюд и пользователей;
- добавление блюда в меню пользователя на выбранный день (одно блюдо
  нельзя добавить в один день дважды);
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
| `/dishes/<id>/` | `dishes.views.dish_detail` | карточка блюда, сколько раз оно в меню |
| `/menu/` | `menu.views.menu_list` | активные записи меню: фильтр по дате, блюду, пользователю, поиск, сортировка, пагинация |
| `/menu/<id>/` | `menu.views.menu_detail` | карточка записи меню |
| `/menu/day/?user=<id>&date=<дата>` | `menu.views.day_menu` | меню пользователя на день, калорийность, блюда, которые можно добавить |
| `/menu/statistics/` | `menu.views.statistics` | статистика по меню и блюдам |

Параметры списка меню: `?date=ГГГГ-ММ-ДД&dish=<id>&user=<id>&q=<текст>&sort=date|dish|user|calories&page=<N>`
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
| `Dish` — блюдо | `dishes/models.py` | `name` (CharField 200), `calories` (PositiveIntegerField ≥ 1), `dish_type` (CharField с choices, по умолчанию «обед») | — |
| `User` — пользователь | `users/models.py` | `name` (CharField 100), `goal` (CharField 200, `blank=True`), `daily_limit` (PositiveIntegerField ≥ 1) | — |
| `MenuEntry` — запись меню | `menu/models.py` | `dish`, `user` (ForeignKey), `menu_date` (DateField), `is_cancelled` (BooleanField, `default=False`) | `dish` → `Dish`, `user` → `User`; `on_delete=PROTECT`, `related_name="menu_entries"` |

Первичные ключи `id` Django создаёт автоматически (`BigAutoField`).
`PROTECT` запрещает удалить блюдо или пользователя, пока на них
ссылаются записи меню, — история меню сохраняется. Обратные связи:
`dish.menu_entries.all()`, `user.menu_entries.all()`. Метод
`MenuEntry.cancel()` отменяет запись (`save(update_fields=[...])`).
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
| 5 | карточка блюда | `get_object_or_404(Dish, pk=dish_id)` | один объект, 404 |
| 6 | карточка блюда | `dish.menu_entries.filter(is_cancelled=False).count()` | обратная связь, подсчёт |
| 7 | список меню | `MenuEntry.objects.filter(is_cancelled=False)` + `.filter(menu_date=...)`, `.filter(dish_id=...)`, `.filter(user_id=...)` | фильтр по нескольким условиям и внешним ключам |
| 8 | список меню | `.filter(Q(dish__name__icontains=q) \| Q(user__name__icontains=q))` | поиск по нескольким полям связанных моделей |
| 9 | список меню | `.annotate(dish_name=F("dish__name"), ...).order_by(...).values(...)` | поля связанных моделей, сортировка по связанному полю, сокращённый набор полей |
| 10 | список меню | `Paginator(entries, 5).get_page(page)` | постраничный вывод |
| 11 | список меню, статистика | `MenuEntry.objects.aggregate(Count("id", filter=Q(...)))` | сводный показатель |
| 12 | запись меню | `get_object_or_404(MenuEntry.objects.select_related("dish", "user"), pk=...)` | связанные объекты одним запросом |
| 13 | меню на день | `.filter(user=user, menu_date=d, is_cancelled=False).select_related("dish")` | несколько условий, `select_related` |
| 14 | меню на день | `day_entries.aggregate(total=Sum("dish__calories"))` | сумма по связанному полю |
| 15 | меню на день | `Dish.objects.exclude(pk__in=day_entries.values_list("dish_id", flat=True))` | исключение `exclude()` |
| 16 | статистика | `Dish.objects.aggregate(Count, Min, Max, Avg)` | агрегирование |
| 17 | статистика | `Dish.objects.values("dish_type").annotate(Count, Avg)` | группировка |
| 18 | статистика | `Dish.objects.annotate(times_planned=Count("menu_entries", filter=Q(...)))` | аннотирование, блюда без записей сохраняются (0) |
| 19 | статистика | `active.values("menu_date", user_name=F(...)).annotate(Count, Sum)` | группировка по пользователю и дате |
| 20 | статистика | `.filter(day_calories__gt=F("daily_limit")).annotate(excess=...)` | условие на агрегат (HAVING) |
| 21 | статистика | `Dish.objects.filter(menu_entries__is_cancelled=False).annotate(Count).filter(times_planned__gt=N)` | фильтр по связанной модели + HAVING |

Поле сортировки выбирается только из словарей `DISH_SORT_FIELDS` и
`ENTRY_SORT_FIELDS`, неизвестное значение заменяется сортировкой по
умолчанию — пользовательский ввод не передаётся в `order_by()`.
Отменённые записи не учитываются ни в списке, ни в меню на день, ни в
статистике.

Поиск по кириллице. Встроенный `LIKE` SQLite не учитывает регистр только
для латиницы, поэтому `homepage/sqlite_unicode.py` при подключении к базе
регистрирует Unicode-версию функции `like()` (сигнал `connection_created`).
Код запросов остаётся стандартным: `name__icontains="овс"` находит
«Овсяная каша».

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
- `dishes/` — модель `Dish`, представления и шаблоны блюд;
- `menu/` — модель `MenuEntry`, представления и шаблоны меню;
- `users/` — модель `User`;
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

Локальная база Django `db.sqlite3` в репозиторий не входит
(`.gitignore`): после клонирования она создаётся миграциями и
заполняется скриптом переноса.

## Требования

- Python 3.x, Django 5.2;
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
python manage.py runserver
```

Сайт: http://127.0.0.1:8000/.

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

На ПР9 слой данных переведён с SQL-запросов через `sqlite3` на Django
ORM: описаны модели `Dish`, `User`, `MenuEntry` со связями, структура
базы создаётся миграциями, данные перенесены из базы ПР7 без потери
связей, все страницы получают данные через ORM. Список меню получил
фильтрацию, поиск, сортировку и постраничный вывод.

## Автор

Журавлев Алексей Игоревич, ЭФБО-12-24.
