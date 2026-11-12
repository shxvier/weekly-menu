"""Общие данные для всех шаблонов проекта."""
from dishes.models import Dish
from menu.models import MenuEntry


def menu_context(request):
    """Название сайта, число блюд и статусы записей меню.

    Ключи словаря становятся переменными любого шаблона, который
    отрисовывается через render() (RequestContext).
    """
    return {
        "site_name": "Меню на неделю",
        # count() считает записи в базе, не загружая объекты.
        "dishes_count": Dish.objects.count(),
        # Константы статусов: {% if entry.status == MenuStatus.CANCELLED %}
        "MenuStatus": MenuEntry.Status,
    }
