"""ПР11: формы фильтрации, создания, редактирования и отмены записей."""
from datetime import date, timedelta
from io import BytesIO
from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.utils import timezone
from PIL import Image

from dishes.models import Dish
from dishes.validators import validate_image_size
from menu.forms import MenuEntryForm, MenuFilterForm
from menu.models import MenuEntry
from users.models import User

pytestmark = pytest.mark.django_db
TAKEN = "Это блюдо уже есть в меню пользователя на выбранную дату."
PAST = "Нельзя запланировать блюдо на прошедшую дату."


def tomorrow():
    return timezone.localdate() + timedelta(days=1)


def entry_data(dish=1, user=1, menu_date=None):
    return {
        "dish": dish,
        "user": user,
        "menu_date": (menu_date or tomorrow()).isoformat(),
    }


def png_file(name="photo.png"):
    buffer = BytesIO()
    Image.new("RGB", (40, 30), (46, 139, 87)).save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), "image/png")


@pytest.fixture
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


# --- форма фильтрации -----------------------------------------------------

def test_filter_form_is_unbound_without_params(client):
    response = client.get("/menu/")
    form = response.context["form"]
    assert not form.is_bound
    assert response.context["error"] is None
    assert response.context["page_obj"].paginator.count == 16


def test_filter_form_cleaned_data_types():
    form = MenuFilterForm({"date": "2026-09-14", "dish": "5", "user": "1",
                           "status": "active", "q": "  греч  ",
                           "sort": "calories"})
    assert form.is_valid()
    data = form.cleaned_data
    assert data["date"] == date(2026, 9, 14)
    assert isinstance(data["dish"], Dish) and data["dish"].pk == 5
    assert isinstance(data["user"], User)
    assert data["q"] == "греч"


@pytest.mark.parametrize("params, field", [
    ({"dish": "999"}, "dish"),
    ({"user": "abc"}, "user"),
    ({"sort": "id;DROP"}, "sort"),
    ({"status": "deleted"}, "status"),
    ({"date": "2026-13-40"}, "date"),
    ({"q": "г"}, "q"),
])
def test_filter_form_rejects_bad_values(client, params, field):
    response = client.get("/menu/", params)
    assert response.status_code == 200
    form = response.context["form"]
    assert field in form.errors
    assert response.context["error"] == (
        "Проверьте введённые значения фильтров."
    )
    # Непроверенные значения не применяются: показан весь список.
    assert response.context["page_obj"].paginator.count == 16


def test_filter_form_keeps_values_in_html(client):
    html = client.get("/menu/?date=2026-09-14&user=1&sort=dish") \
        .content.decode()
    assert 'value="2026-09-14"' in html
    assert '<option value="1" selected>Анна</option>' in html
    assert '<option value="dish" selected>блюду</option>' in html


# --- создание записи ------------------------------------------------------

def test_create_form_get_has_initial_date_and_csrf(client):
    response = client.get("/menu/create/")
    assert response.status_code == 200
    form = response.context["form"]
    assert not form.is_bound
    assert form.initial["menu_date"] == timezone.localdate()
    html = response.content.decode()
    assert "csrfmiddlewaretoken" in html
    assert 'type="date"' in html and 'class="form-select"' in html
    assert list(form.fields) == ["dish", "menu_date", "user"]


def test_create_prefills_from_day_menu(client):
    day = tomorrow().isoformat()
    form = client.get(f"/menu/create/?dish=6&user=2&date={day}") \
        .context["form"]
    assert form.initial == {"dish": 6, "user": 2, "menu_date": tomorrow()}
    html = client.get(f"/menu/day/?user=1&date={day}").content.decode()
    assert f"/menu/create/?dish=6&amp;user=1&amp;date={day}" in html


def test_create_saves_entry_and_redirects(client):
    response = client.post("/menu/create/", entry_data())
    entry = MenuEntry.objects.latest("pk")
    assert response.status_code == 302
    assert response["Location"] == f"/menu/{entry.pk}/"
    assert entry.dish_id == 1 and entry.user_id == 1
    assert entry.menu_date == tomorrow()
    assert entry.status == MenuEntry.Status.ACTIVE
    assert MenuEntry.objects.count() == 18
    html = client.get(response["Location"]).content.decode()
    assert "Запись добавлена в меню." in html


def test_create_rejects_past_date(client):
    yesterday = timezone.localdate() - timedelta(days=1)
    response = client.post("/menu/create/", entry_data(menu_date=yesterday))
    assert response.status_code == 200
    assert response.context["form"].errors["menu_date"] == [PAST]
    assert PAST in response.content.decode()
    assert MenuEntry.objects.count() == 17


def test_create_required_fields(client):
    form = client.post("/menu/create/", {}).context["form"]
    assert set(form.errors) == {"dish", "menu_date", "user"}


def test_create_rejects_dish_already_in_day_menu(client):
    client.post("/menu/create/", entry_data())
    response = client.post("/menu/create/", entry_data())
    assert response.context["form"].non_field_errors() == [TAKEN]
    assert TAKEN in response.content.decode()
    assert MenuEntry.objects.count() == 18
    # Другому пользователю то же блюдо добавить можно.
    assert client.post("/menu/create/", entry_data(user=2)) \
        .status_code == 302


def test_cancelled_entry_does_not_block_dish(client):
    client.post("/menu/create/", entry_data())
    MenuEntry.objects.latest("pk").cancel()
    response = client.post("/menu/create/", entry_data())
    assert response.status_code == 302
    assert MenuEntry.objects.in_menu().filter(
        dish_id=1, user_id=1, menu_date=tomorrow(),
    ).count() == 1


def test_completed_entry_blocks_dish(client):
    client.post("/menu/create/", entry_data())
    MenuEntry.objects.filter(pk=MenuEntry.objects.latest("pk").pk) \
        .update(status=MenuEntry.Status.COMPLETED)
    response = client.post("/menu/create/", entry_data())
    assert response.context["form"].non_field_errors() == [TAKEN]


def test_clean_checks_dish_against_daily_limit():
    user = User.objects.create(name="Пётр", daily_limit=300)
    form = MenuEntryForm(entry_data(dish=1, user=user.pk))
    assert not form.is_valid()
    assert form.non_field_errors() == [
        "Калорийность блюда (320 ккал) больше дневного лимита "
        "пользователя (300 ккал)."
    ]
    assert MenuEntryForm(entry_data(dish=3, user=user.pk)).is_valid()


# --- редактирование -------------------------------------------------------

def test_update_form_is_filled_with_instance(client):
    response = client.get("/menu/10/edit/")
    form = response.context["form"]
    assert form.instance.pk == 10
    assert form.initial["dish"] == 5 and form.initial["user"] == 2
    html = response.content.decode()
    assert "Редактирование записи №10" in html
    assert 'value="2026-09-14"' in html
    assert "Сохранить изменения" in html


def test_update_without_changes_keeps_one_record(client):
    entry = MenuEntry.objects.get(pk=1)
    data = entry_data(entry.dish_id, entry.user_id, entry.menu_date)
    response = client.post("/menu/1/edit/", data)
    assert response.status_code == 302
    assert response["Location"] == "/menu/1/"
    assert MenuEntry.objects.count() == 17


def test_update_changes_existing_record(client):
    # Запись №1: Анна, 14.09.2026, овсяная каша -> йогурт (свободен).
    data = entry_data(9, 1, date(2026, 9, 14))
    response = client.post("/menu/1/edit/", data)
    assert response.status_code == 302
    entry = MenuEntry.objects.get(pk=1)
    assert entry.dish_id == 9 and entry.status == MenuEntry.Status.ACTIVE
    assert MenuEntry.objects.count() == 17
    client.post("/menu/1/edit/", entry_data(9, 1, tomorrow()))
    assert MenuEntry.objects.get(pk=1).menu_date == tomorrow()


def test_update_rejects_conflict_with_other_entry(client):
    # В тот же день у Анны уже есть гречка (запись №2).
    data = entry_data(5, 1, date(2026, 9, 14))
    response = client.post("/menu/1/edit/", data)
    assert response.context["form"].non_field_errors() == [TAKEN]
    assert MenuEntry.objects.get(pk=1).dish_id == 1


def test_update_rejects_moving_to_past_date(client):
    response = client.post("/menu/1/edit/", entry_data(1, 1, date(2026, 9, 1)))
    assert response.context["form"].errors["menu_date"] == [PAST]
    assert MenuEntry.objects.get(pk=1).menu_date == date(2026, 9, 14)


@pytest.mark.parametrize("url", ["/menu/999/edit/", "/menu/9/edit/"])
def test_update_missing_or_cancelled_entry_is_404(client, url):
    # №9 отменена: изменить её по прямому адресу нельзя.
    assert client.get(url).status_code == 404


# --- отмена ---------------------------------------------------------------

def test_cancel_via_get_is_not_allowed(client):
    assert client.get("/menu/1/cancel/").status_code == 405
    assert MenuEntry.objects.get(pk=1).status == MenuEntry.Status.ACTIVE


def test_cancel_changes_status_and_keeps_record(client):
    response = client.post("/menu/1/cancel/")
    assert response.status_code == 302 and response["Location"] == "/menu/"
    entry = MenuEntry.objects.get(pk=1)
    assert entry.status == MenuEntry.Status.CANCELLED
    assert MenuEntry.objects.count() == 17
    assert 1 not in [row["id"] for row in
                     client.get("/menu/?date=2026-09-14")
                     .context["entries"]]
    # Повторная отмена: активной записи уже нет.
    assert client.post("/menu/1/cancel/").status_code == 404
    # Блюдо освободилось в меню дня.
    free = client.get("/menu/day/?user=1&date=2026-09-14") \
        .context["free_dishes"]
    assert 1 in [dish.pk for dish in free]


def test_cancel_returns_to_same_list_page(client):
    response = client.post("/menu/2/cancel/",
                           {"next": "/menu/?user=1&page=2"})
    assert response["Location"] == "/menu/?user=1&page=2"
    response = client.post("/menu/3/cancel/",
                           {"next": "https://example.com/"})
    assert response["Location"] == "/menu/"


def test_post_without_csrf_token_is_rejected():
    csrf_client = Client(enforce_csrf_checks=True)
    assert csrf_client.post("/menu/1/cancel/").status_code == 403
    assert csrf_client.post("/menu/create/", entry_data()).status_code == 403
    assert MenuEntry.objects.get(pk=1).status == MenuEntry.Status.ACTIVE


def test_list_shows_actions_only_for_active(client):
    html = client.get("/menu/?status=cancelled").content.decode()
    assert "/menu/9/cancel/" not in html and "/menu/9/edit/" not in html
    html = client.get("/menu/?date=2026-09-14").content.decode()
    assert 'action="/menu/1/cancel/"' in html
    assert 'href="/menu/1/edit/"' in html
    assert 'href="/menu/create/"' in html
    assert "csrfmiddlewaretoken" in html


def test_filters_sort_pagination_after_create(client):
    client.post("/menu/create/", entry_data(dish=6, user=2))
    response = client.get("/menu/?user=2&sort=calories")
    ids = [row["id"] for row in response.context["entries"]]
    assert len(ids) == 3 and ids[0] == MenuEntry.objects.latest("pk").pk
    assert client.get("/menu/").context["page_obj"].paginator.num_pages == 4
    assert client.get("/menu/?page=4").context["page_obj"] \
        .paginator.count == 17


# --- блюда и загрузка изображений ----------------------------------------

def test_dish_create_with_image(client, media_root):
    response = client.post("/dishes/create/", {
        "name": "Сырники со сметаной", "calories": 410,
        "dish_type": "завтрак", "image": png_file(),
    })
    dish = Dish.objects.get(name="Сырники со сметаной")
    assert response.status_code == 302
    assert response["Location"] == dish.get_absolute_url()
    assert dish.image.name.startswith("dishes/")
    assert (media_root / dish.image.name).is_file()
    html = client.get(dish.get_absolute_url()).content.decode()
    assert f'src="/media/{dish.image.name}"' in html


def test_dish_without_image_shows_message(client, media_root):
    client.post("/dishes/create/", {
        "name": "Тыквенный суп", "calories": 180, "dish_type": "обед",
    })
    dish = Dish.objects.get(name="Тыквенный суп")
    assert not dish.image
    html = client.get(dish.get_absolute_url()).content.decode()
    assert "Фотография не загружена." in html


def test_dish_form_has_multipart_enctype(client):
    html = client.get("/dishes/create/").content.decode()
    assert 'enctype="multipart/form-data"' in html
    assert 'type="file"' in html


def test_dish_form_rejects_non_image(client, media_root):
    fake = SimpleUploadedFile("photo.png", b"not an image", "image/png")
    response = client.post("/dishes/create/", {
        "name": "Фальшивка", "calories": 100, "dish_type": "обед",
        "image": fake,
    })
    assert "image" in response.context["form"].errors
    assert not Dish.objects.filter(name="Фальшивка").exists()


def test_image_size_validator():
    validate_image_size(SimpleNamespace(size=2 * 1024 * 1024))
    with pytest.raises(ValidationError):
        validate_image_size(SimpleNamespace(size=2 * 1024 * 1024 + 1))


def test_dish_form_rejects_duplicate_name(client):
    response = client.post("/dishes/create/", {
        "name": "  греческий   САЛАТ ", "calories": 200,
        "dish_type": "обед",
    })
    assert response.context["form"].errors["name"] == [
        "Блюдо с таким названием уже есть."
    ]


def test_dish_update_replaces_image_and_keeps_slug(client, media_root):
    dish = Dish.objects.get(pk=3)
    url = "/dishes/grecheskii-salat-3/edit/"
    form = client.get(url).context["form"]
    assert form.initial["name"] == "Греческий салат"
    client.post(url, {"name": "Греческий салат", "calories": 260,
                      "dish_type": "ужин", "image": png_file("a.png")})
    dish.refresh_from_db()
    first = dish.image.name
    assert dish.calories == 260 and dish.slug == "grecheskii-salat-3"
    client.post(url, {"name": "Греческий салат", "calories": 260,
                      "dish_type": "ужин", "image": png_file("b.png")})
    dish.refresh_from_db()
    assert dish.image.name != first
    assert dish.image.name.startswith("dishes/b")
    assert Dish.objects.count() == 9


def test_dish_update_missing_slug_is_404(client):
    assert client.get("/dishes/no-such-dish-1/edit/").status_code == 404


def test_admin_dish_page_has_image_field(client):
    from django.contrib.auth import get_user_model

    get_user_model().objects.create_superuser("adm", "a@example.com", "pw")
    client.login(username="adm", password="pw")
    html = client.get("/admin/dishes/dish/3/change/").content.decode()
    assert 'name="image"' in html
    assert "Фотография не загружена" in html
