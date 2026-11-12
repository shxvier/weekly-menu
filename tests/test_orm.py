"""ПР9: модели, связи, перенос данных и ORM-запросы представлений."""
import re
from datetime import date
from pathlib import Path

import pytest
from django.db.models import ProtectedError

from dishes.models import Dish
from menu.models import MenuEntry
from users.models import User

pytestmark = pytest.mark.django_db
ROOT = Path(__file__).resolve().parent.parent


def entry_ids(response):
    return [row["id"] for row in response.context["entries"]]


# --- модели и связи -------------------------------------------------------

def test_models_fields_and_str():
    dish = Dish.objects.get(pk=1)
    assert str(dish) == "Овсяная каша с ягодами"
    assert dish.calories == 320 and dish.dish_type == "завтрак"
    assert dish.fits_limit(320) and not dish.fits_limit(300)
    assert Dish._meta.get_field("dish_type").default == "обед"
    assert User._meta.get_field("goal").blank is True
    assert str(MenuEntry.objects.get(pk=1)).startswith("Овсяная каша")


def test_foreign_keys_and_reverse_relations():
    entry = MenuEntry.objects.select_related("dish", "user").get(pk=10)
    assert entry.dish.name == "Гречка с индейкой"
    assert entry.user.name == "Иван"
    assert entry.dish_id == 5
    dish = Dish.objects.get(pk=5)
    assert dish.menu_entries.count() == 3
    assert User.objects.get(pk=2).menu_entries.count() == 2


def test_import_keeps_ids_dates_and_statuses():
    assert Dish.objects.count() == 9
    assert User.objects.count() == 2
    assert MenuEntry.objects.count() == 17
    assert MenuEntry.objects.get(pk=9).is_cancelled is True
    assert MenuEntry.objects.get(pk=1).menu_date == date(2026, 9, 14)


def test_crud_and_cancel():
    dish = Dish.objects.create(name="Тестовый суп", calories=150)
    assert dish.dish_type == "обед"
    dish.calories = 180
    dish.save()
    assert Dish.objects.get(pk=dish.pk).calories == 180
    entry = MenuEntry.objects.create(
        dish=dish, user_id=1, menu_date=date(2026, 9, 20),
    )
    entry.cancel()
    assert MenuEntry.objects.get(pk=entry.pk).is_cancelled is True
    entry.delete()
    dish.delete()
    assert not Dish.objects.filter(name="Тестовый суп").exists()


def test_protect_forbids_deleting_used_dish():
    with pytest.raises(ProtectedError):
        Dish.objects.get(pk=5).delete()


# --- список блюд ----------------------------------------------------------

def test_dish_search_is_case_insensitive_for_cyrillic(client):
    response = client.get("/dishes/?q=овс")
    names = [d.name for d in response.context["dishes"]]
    assert names == ["Овсяная каша с ягодами"]
    assert Dish.objects.filter(name__icontains="СЁМГ").count() == 1


def test_dish_sorting_by_whitelist(client):
    light = client.get("/dishes/?sort=calories").context["dishes"]
    assert light[0].calories == 190
    heavy = client.get("/dishes/?sort=-calories").context["dishes"]
    assert heavy[0].calories == 560
    unknown = client.get("/dishes/?sort=id;DROP").context
    assert unknown["sort"] == "name"
    assert unknown["dishes"][0].name == "Греческий салат"


# --- список меню: фильтры, поиск, сортировка, пагинация ------------------

def test_menu_filters_by_user_date_and_dish(client):
    assert entry_ids(client.get("/menu/?user=2")) == [10, 11]
    assert sorted(entry_ids(client.get("/menu/?date=2026-09-15"))) == [4, 5, 6]
    assert entry_ids(client.get("/menu/?dish=5&user=1")) == [2, 13]


def test_menu_search_by_dish_or_user_name(client):
    assert entry_ids(client.get("/menu/?q=иван")) == [10, 11]
    ids = entry_ids(client.get("/menu/?q=греч"))
    assert set(ids) == {2, 8, 10, 13}


def test_menu_sorting(client):
    rows = client.get("/menu/?date=2026-09-14&sort=calories").context
    calories = [row["calories"] for row in rows["entries"]]
    assert calories == sorted(calories, reverse=True)
    rows = client.get("/menu/?sort=dish").context["entries"]
    names = [row["dish_name"] for row in rows]
    assert names == sorted(names)
    assert client.get("/menu/?sort=bad").context["sort"] == "date"


def test_menu_excludes_cancelled_entries(client):
    response = client.get("/menu/?date=2026-09-16")
    assert 9 not in entry_ids(response)


def test_menu_pagination(client):
    first = client.get("/menu/")
    assert first.context["page_obj"].paginator.num_pages == 4
    assert len(entry_ids(first)) == 5
    assert entry_ids(client.get("/menu/?page=4")) == [17]
    assert client.get("/menu/?page=abc").context["page_obj"].number == 1
    assert client.get("/menu/?page=99").context["page_obj"].number == 4


def test_pagination_links_keep_filters(client):
    html = client.get("/menu/?user=1&sort=dish&page=2").content.decode()
    links = re.findall(r'href="(\?[^"]*)"', html)
    assert "?user=1&amp;sort=dish&amp;page=3" in links


def test_menu_bad_date(client):
    html = client.get("/menu/?date=31-31-2026").content.decode()
    assert "Укажите корректную дату." in html


# --- меню на день и статистика -------------------------------------------

def test_cancelled_entry_does_not_block_dish(client):
    response = client.get("/menu/day/?user=1&date=2026-09-16")
    free = [d.pk for d in response.context["free_dishes"]]
    assert 6 in free
    assert 1 not in free and 3 not in free


def test_statistics_keeps_dishes_without_entries(client):
    rows = client.get("/menu/statistics/").context["popularity"]
    by_name = {row["dish_name"]: row["times_planned"] for row in rows}
    assert by_name["Йогурт с орехами"] == 0
    assert by_name["Гречка с индейкой"] == 3
    assert len(by_name) == 9


def test_statistics_aggregates(client):
    context = client.get("/menu/statistics/").context
    assert context["counts"] == {
        "total_entries": 17, "active_entries": 16, "cancelled_entries": 1,
    }
    assert context["calories_range"]["min_calories"] == 190
    over = list(context["over_limit"])
    assert len(over) == 1 and over[0]["excess"] == 150


def test_views_do_not_use_sqlite3_or_json():
    for name in ("dishes/views.py", "menu/views.py"):
        code = (ROOT / name).read_text(encoding="utf-8")
        assert "sqlite3" not in code
        assert "storage" not in code
