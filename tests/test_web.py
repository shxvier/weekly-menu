import pytest
from django.test import Client, override_settings


@pytest.fixture
def client():
    return Client()


@pytest.mark.parametrize("url", [
    "/", "/dishes/", "/dishes/1/", "/menu/", "/menu/1/",
])
def test_pages_open(client, url):
    response = client.get(url)
    assert response.status_code == 200
    assert "bootstrap" in response.content.decode().lower()


def test_list_shows_domain_data(client):
    html = client.get("/dishes/").content.decode()
    assert "Овсяная каша с ягодами" in html
    assert "320 ккал" in html


def test_menu_shows_statuses(client):
    html = client.get("/menu/").content.decode().lower()
    assert "отменено" in html
    assert "активно" in html


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
