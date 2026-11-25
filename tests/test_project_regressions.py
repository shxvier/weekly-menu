from datetime import timedelta
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.utils import timezone
from PIL import Image

from dishes.models import Dish
from menu.models import TAKEN_ERROR, MenuEntry
from users.models import User

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("value", ["²", "9" * 4500])
def test_invalid_numeric_parameters_do_not_return_500(client, value):
    create = client.get("/menu/create/", {"dish": value, "user": value})
    assert create.status_code == 200
    assert "dish" not in create.context["form"].initial
    day = client.get("/menu/day/", {"user": value, "date": "2026-09-14"})
    assert day.status_code == 200
    assert day.context["error"] == "Выберите пользователя."
    stats = client.get("/menu/statistics/", {"min_count": value})
    assert stats.status_code == 200
    assert stats.context["threshold"] == 2


def test_statistics_keep_same_name_users_separate(client):
    first = User.objects.get(pk=1)
    second = User.objects.create(
        name=first.name, daily_limit=first.daily_limit,
    )
    menu_date = MenuEntry.objects.get(pk=1).menu_date
    MenuEntry.objects.create(
        user=second, dish_id=1, menu_date=menu_date,
    )
    page = client.get("/menu/statistics/")
    same_day = {
        row["user_id"]: row["day_calories"]
        for row in page.context["calories_by_day"]
        if row["menu_date"] == menu_date
    }
    assert same_day[first.pk] == 1330
    assert same_day[second.pk] == 320


def test_database_enforces_one_dish_per_user_and_date():
    entry = MenuEntry.objects.get(pk=1)
    slot = {
        "dish_id": entry.dish_id,
        "user_id": entry.user_id,
        "menu_date": entry.menu_date,
    }
    MenuEntry.objects.create(**slot, status=MenuEntry.Status.CANCELLED)
    with pytest.raises(IntegrityError), transaction.atomic():
        MenuEntry.objects.create(**slot, status=MenuEntry.Status.COMPLETED)
    entry.cancel()
    MenuEntry.objects.create(**slot)
    assert MenuEntry.objects.in_menu().matching_slot(**slot).count() == 1


def test_admin_skips_restoring_cancelled_duplicate(admin_client):
    active = MenuEntry.objects.get(pk=1)
    cancelled = MenuEntry.objects.create(
        dish_id=active.dish_id,
        user_id=active.user_id,
        menu_date=active.menu_date,
        status=MenuEntry.Status.CANCELLED,
    )
    url = "/admin/menu/menuentry/"
    edit = admin_client.post(f"{url}{cancelled.pk}/change/", {
        "dish": active.dish_id,
        "user": active.user_id,
        "menu_date": active.menu_date.isoformat(),
        "status": MenuEntry.Status.ACTIVE,
    })
    assert TAKEN_ERROR in edit.content.decode()
    response = admin_client.post(url, {
        "action": "restore_entries",
        "_selected_action": [cancelled.pk, 17],
    }, follow=True)
    assert response.status_code == 200
    assert "Пропущено записей" in response.content.decode()
    cancelled.refresh_from_db()
    assert cancelled.status == MenuEntry.Status.CANCELLED
    assert MenuEntry.objects.get(pk=17).status == MenuEntry.Status.ACTIVE


def test_day_menu_only_offers_dishes_that_can_be_added(client):
    user = User.objects.create(name="Лимит", daily_limit=1)
    today = timezone.localdate()
    day = client.get("/menu/day/", {"user": user.pk, "date": today})
    assert not list(day.context["free_dishes"])
    yesterday = today - timedelta(days=1)
    past = client.get("/menu/day/", {"user": 1, "date": yesterday})
    assert 'href="/menu/create/?dish=' not in past.content.decode()


def test_transliterated_slug_fits_model_field():
    dish = Dish.objects.create(name="Щ" * 200, calories=10)
    assert len(dish.slug) <= Dish._meta.get_field("slug").max_length
    assert dish.slug.endswith(f"-{dish.pk}")
    assert dish.get_absolute_url() == f"/dishes/{dish.slug}/"


def test_new_dish_can_be_saved_again_after_database_failure():
    dish = Dish(name="Повторное сохранение", calories=-1)
    with pytest.raises(IntegrityError):
        dish.save()
    assert dish.pk is None
    assert not dish.slug
    dish.calories = 100
    dish.save()
    assert dish.slug == f"povtornoe-sokhranenie-{dish.pk}"


@pytest.mark.parametrize("admin_form", [False, True])
def test_upload_requires_supported_format_and_matching_extension(
    request, client, admin_form,
):
    buffer = BytesIO()
    Image.new("RGB", (20, 20)).save(buffer, format="GIF")
    url = "/dishes/create/"
    if admin_form:
        client = request.getfixturevalue("admin_client")
        url = "/admin/dishes/dish/add/"
    upload = SimpleUploadedFile("photo.png", buffer.getvalue(), "image/png")
    response = client.post(url, {
        "name": "Проверка формата",
        "calories": 100,
        "dish_type": "завтрак",
        "image": upload,
    })
    assert response.status_code == 200
    assert "с соответствующим расширением" in response.content.decode()
    assert not Dish.objects.filter(name="Проверка формата").exists()
