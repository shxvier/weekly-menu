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

Используется фреймворк Django 5.2. С ПР7 веб-слой получает данные из
базы SQLite SQL-запросами (модуль `sqlite3`, без Django ORM). Страницы строятся
системой шаблонов Django (DTL): представления только готовят данные
и передают их в шаблон через `render(request, шаблон, context)`.
Функция `page()` из ПР5 удалена — HTML в Python больше не собирается.

Django-проект — `weeklymenu/`, приложения:

- `homepage` — главная страница и страница ошибки 404;
- `dishes` — страницы блюд;
- `menu` — страницы записей меню.

| URL | View | Страница |
|-----|------|----------|
| `/` | `homepage.views.index` | главная, навигация |
| `/dishes/` | `dishes.views.dish_list` | список блюд |
| `/dishes/<id>/` | `dishes.views.dish_detail` | карточка блюда, статус на сегодня |
| `/menu/` | `menu.views.menu_list` | список записей меню со статусами |
| `/menu/<id>/` | `menu.views.menu_detail` | карточка записи меню |
| `/menu/day/?user=<id>&date=<дата>` | `menu.views.day_menu` | меню пользователя на день, калорийность, блюда, которые можно добавить |
| `/menu/statistics/` | `menu.views.statistics` | статистика по меню и блюдам |

На странице `/dishes/` есть форма подбора блюд по лимиту калорий
(`?max_calories=300`).

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

## База данных (SQLite, ПР7)

Файл базы — `data/weekly_menu.sqlite`. JSON-файлы остаются исходными
данными консольной версии и источником для импорта.

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

### SQL в веб-приложении

Представления `dishes/views.py` и `menu/views.py` выполняют запросы
из `sql/queries.sql`; значения от пользователя (лимит калорий, дата,
пользователь, порог частоты) передаются только параметрами `?`, без
f-строк. Строки результата — `sqlite3.Row`, поэтому в шаблонах поля
доступны по имени: `{{ dish.name }}`, `{{ entry.dish_name }}`.

## Структура проекта

- `manage.py` — управление Django-проектом;
- `weeklymenu/` — настройки и корневые маршруты Django;
- `homepage/`, `dishes/`, `menu/` — Django-приложения (views,
  urls, шаблоны; статика — в `homepage/static/`);
- `templates/` — общие шаблоны проекта;
- `db/` — подключение к SQLite и импорт из JSON;
- `sql/` — схема БД и SQL-запросы;
- `main.py` — точка запуска консольного меню;
- `models/` — пакет предметной области:
  - `dishes.py` — класс `Dish` и функции работы с блюдами;
  - `users.py` — класс `User` и функции работы с пользователями;
  - `menu.py` — класс `MenuEntry` и функции работы с меню;
- `storage.py` — сохранение и загрузка данных (JSON);
- `utils.py` — вспомогательные функции (даты, безопасный ввод);
- `data/` — JSON-файлы данных (`dishes.json`, `users.json`,
  `menu.json`);
- `tests/` — автоматизированные тесты.

## Требования

- Python 3.x;
- pytest;
- flake8.

Установка зависимостей:

```
pip install -r requirements.txt
```

## Запуск программы

```
python main.py
```

## Запуск тестов

```
pytest -v
```

## Проверка качества кода

```
flake8 . --extend-exclude=venv
```

## Текущий этап разработки

На ПР7 данные проекта перенесены из JSON в SQLite: база
`data/weekly_menu.sqlite` создаётся по `sql/schema.sql` и заполняется
скриптом `db/import_json.py`, запросы хранятся в `sql/queries.sql`,
Django-представления получают данные из SQLite и отображают их на
страницах «Блюда», «Меню», «Меню на день» и «Статистика».
Консольная версия по-прежнему работает с JSON.

На следующих практических работах база будет подключена к Django
через Django ORM.
