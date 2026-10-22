import pytest
from django.test import Client, override_settings


@pytest.fixture
def client():
    return Client()


@pytest.mark.parametrize("url", [
    "/", "/dishes/", "/dishes/1/", "/menu/", "/menu/1/",
    "/menu/day/", "/menu/statistics/",
])
def test_pages_open(client, url):
    response = client.get(url)
    assert response.status_code == 200
    assert "bootstrap" in response.content.decode().lower()


def test_list_shows_domain_data(client):
    html = client.get("/dishes/").content.decode()
    assert "Овсяная каша с ягодами" in html
    assert "320 ккал" in html


def test_menu_shows_only_active_entries(client):
    html = client.get("/menu/").content.decode()
    assert "Активных записей: 16" in html
    assert "отменённых: 1" in html
    assert 'href="/menu/9/"' not in html


def test_detail_pages_show_related_objects(client):
    html = client.get("/menu/10/").content.decode()
    assert "Гречка с индейкой" in html
    assert "Иван" in html


def test_missing_dish_gives_404(client):
    response = client.get("/dishes/999/")
    assert response.status_code == 404
    assert "Блюдо не найдено" in response.content.decode()


def test_missing_menu_entry_gives_404(client):
    response = client.get("/menu/999/")
    assert response.status_code == 404
    assert "Запись меню не найдена" in response.content.decode()


@override_settings(DEBUG=False)
def test_custom_404_page(client):
    response = client.get("/nonexistent/")
    assert response.status_code == 404
    assert "404 – страница не найдена" in response.content.decode()


def test_pages_use_base_template_and_static(client):
    html = client.get("/").content.decode()
    assert "homepage/css/style.css" in html
    assert "homepage/js/main.js" in html
    assert "homepage/img/logo.png" in html
    assert 'id="current-year"' in html


def test_dish_list_uses_filters_and_cards(client):
    response = client.get("/dishes/")
    html = response.content.decode()
    assert "Всего блюд: 9" in html
    assert html.count("dish-card") == 9
    first = response.context["dishes"][0]
    assert first["name"] == "Греческий салат"


def test_named_urls_in_navigation(client):
    html = client.get("/menu/").content.decode()
    assert 'href="/dishes/"' in html
    assert 'href="/menu/1/"' in html


def test_dish_filter_is_parameterized(client):
    html = client.get("/dishes/?max_calories=250").content.decode()
    assert "Блюд не больше 250 ккал: 3" in html
    assert "Овсяная каша" not in html
    html = client.get("/dishes/?max_calories=abc").content.decode()
    assert "положительным числом" in html


def test_dish_detail_counts_plans(client):
    html = client.get("/dishes/5/").content.decode()
    assert "Гречка с индейкой" in html
    assert '<span class="badge bg-success">3</span>' in html


def test_day_menu_page(client):
    response = client.get("/menu/day/")
    assert response.status_code == 200
    assert "Пользователь" in response.content.decode()
    html = client.get("/menu/day/?user=1&date=2026-09-14").content.decode()
    assert "1330" in html
    assert "осталось 670 ккал" in html
    assert "Греческий салат" in html


def test_day_menu_shows_excess(client):
    html = client.get("/menu/day/?user=1&date=2026-09-17").content.decode()
    assert "превышение на 150 ккал" in html


def test_day_menu_empty_and_bad_input(client):
    html = client.get("/menu/day/?user=2&date=2026-10-01").content.decode()
    assert "На этот день блюд в меню нет." in html
    html = client.get("/menu/day/?user=1&date=завтра").content.decode()
    assert "Укажите корректную дату." in html


def test_statistics_page(client):
    response = client.get("/menu/statistics/")
    html = response.content.decode()
    assert response.status_code == 200
    assert "Анна, 2026-09-17" in html
    assert "+150" in html
    assert len(response.context["frequent"]) == 2
    response = client.get("/menu/statistics/?min_count=5")
    assert "Таких блюд нет." in response.content.decode()


def test_page_function_removed():
    import homepage.views
    assert not hasattr(homepage.views, "page")
