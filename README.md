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

Используется фреймворк Django 5.2. Веб-слой берёт данные из тех же
JSON-файлов и использует классы пакета `models/`. Страницы строятся
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
python manage.py migrate
python manage.py runserver
```

После этого сайт доступен по адресу http://127.0.0.1:8000/.

## Структура проекта

- `manage.py` — управление Django-проектом;
- `weeklymenu/` — настройки и корневые маршруты Django;
- `homepage/`, `dishes/`, `menu/` — Django-приложения (views,
  urls, шаблоны; статика — в `homepage/static/`);
- `templates/` — общие шаблоны проекта;
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
