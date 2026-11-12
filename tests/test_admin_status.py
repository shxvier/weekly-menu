"""ПР10: административная панель, менеджер и статусы записей меню."""
from datetime import date

import pytest
from django.contrib.auth import get_user_model

from menu.models import MenuEntry

pytestmark = pytest.mark.django_db
DAY = date(2026, 9, 14)


@pytest.fixture
def admin_client(client):
    get_user_model().objects.create_superuser(
        "admin", "admin@example.com", "pass12345",
    )
    client.login(username="admin", password="pass12345")
    return client


# --- менеджер и статусы ---------------------------------------------------

def test_manager_methods_split_by_status():
    MenuEntry.objects.filter(pk=1).update(status=MenuEntry.Status.COMPLETED)
    total = MenuEntry.objects.count()
    active = MenuEntry.objects.active().count()
    cancelled = MenuEntry.objects.cancelled().count()
    completed = MenuEntry.objects.completed().count()
    assert (active, cancelled, completed) == (15, 1, 1)
    assert active + cancelled + completed == total
    assert MenuEntry.objects.in_menu().count() == 16
    ids = list(MenuEntry.objects.active().for_date(DAY)
               .values_list("id", flat=True))
    assert 1 not in ids and 2 in ids


def test_completed_entry_stays_in_day_menu(client):
    MenuEntry.objects.filter(pk=1).update(status=MenuEntry.Status.COMPLETED)
    context = client.get("/menu/day/?user=1&date=2026-09-14").context
    assert context["day_calories"] == 1330
    assert 1 not in [d.pk for d in context["free_dishes"]]


def test_cancelled_entry_frees_dish(client):
    MenuEntry.objects.get(pk=1).cancel()
    context = client.get("/menu/day/?user=1&date=2026-09-14").context
    assert context["day_calories"] == 1010
    assert 1 in [d.pk for d in context["free_dishes"]]


def test_statistics_counts_each_status(client):
    MenuEntry.objects.filter(pk=2).update(status=MenuEntry.Status.COMPLETED)
    MenuEntry.objects.get(pk=3).cancel()
    counts = client.get("/menu/statistics/").context["counts"]
    assert counts == {
        "total_entries": 17, "active_entries": 14,
        "completed_entries": 1, "cancelled_entries": 2,
    }


def test_status_badges_in_list(client):
    MenuEntry.objects.filter(pk=1).update(status=MenuEntry.Status.COMPLETED)
    html = client.get("/menu/?date=2026-09-14").content.decode()
    assert "Выполнено" in html and "Запланировано" in html


# --- административная панель ---------------------------------------------

@pytest.mark.parametrize("url", [
    "/admin/",
    "/admin/dishes/dish/",
    "/admin/dishes/dish/5/change/",
    "/admin/users/user/",
    "/admin/users/user/1/change/",
    "/admin/menu/menuentry/",
    "/admin/menu/menuentry/10/change/",
    "/admin/menu/menuentry/?menu_date__year=2026&menu_date__month=9",
])
def test_admin_pages_open(admin_client, url):
    assert admin_client.get(url).status_code == 200


def test_admin_search_and_filter(admin_client):
    response = admin_client.get("/admin/menu/menuentry/?q=иван")
    assert {e.pk for e in response.context["cl"].result_list} == {10, 11}
    response = admin_client.get("/admin/menu/menuentry/?status=cancelled")
    assert [e.pk for e in response.context["cl"].result_list] == [9]


def test_admin_dish_list_annotation(admin_client):
    response = admin_client.get("/admin/dishes/dish/")
    counts = {d.name: d.in_menu_count
              for d in response.context["cl"].result_list}
    assert counts["Гречка с индейкой"] == 3
    assert counts["Йогурт с орехами"] == 0


def test_admin_actions(admin_client):
    url = "/admin/menu/menuentry/"
    admin_client.post(url, {
        "action": "cancel_entries", "_selected_action": ["1", "2"],
    })
    assert MenuEntry.objects.cancelled().count() == 3
    admin_client.post(url, {
        "action": "complete_entries", "_selected_action": ["4"],
    })
    assert MenuEntry.objects.get(pk=4).status == "completed"
    admin_client.post(url, {
        "action": "restore_entries", "_selected_action": ["1", "2", "4"],
    })
    assert MenuEntry.objects.active().count() == 16


def test_admin_requires_login(client):
    response = client.get("/admin/menu/menuentry/")
    assert response.status_code == 302
    assert "/admin/login/" in response["Location"]
