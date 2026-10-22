import pytest

from dishes import (
    add_dish,
    check_dish_calories,
    filter_dishes_by_calories,
    find_dish,
    sort_dishes,
)


def make_dishes() -> dict:
    dishes: dict = {}
    add_dish(dishes, "Овсяная каша", 320, "завтрак")
    add_dish(dishes, "Греческий салат", 250, "обед")
    add_dish(dishes, "Сёмга с рисом", 560, "ужин")
    return dishes


def test_add_dish():
    dishes: dict = {}
    add_dish(dishes, "Овсяная каша", 320, "завтрак")
    assert len(dishes) == 1
    assert dishes[1]["name"] == "Овсяная каша"


def test_add_dish_ids_increase():
    assert list(make_dishes()) == [1, 2, 3]


def test_add_dish_rejects_bad_data():
    with pytest.raises(ValueError):
        add_dish({}, "   ", 100, "обед")
    with pytest.raises(ValueError):
        add_dish({}, "Суп", 0, "обед")


def test_find_dish_ignores_case():
    assert find_dish(make_dishes(), "ОВСЯНАЯ")
    assert find_dish(make_dishes(), "пицца") == []


def test_check_dish_calories():
    dishes = make_dishes()
    assert check_dish_calories(dishes, 2, 300)
    assert not check_dish_calories(dishes, 3, 300)


def test_check_dish_calories_unknown_dish():
    with pytest.raises(KeyError):
        check_dish_calories(make_dishes(), 99, 300)


def test_filter_dishes_by_calories():
    names = [d["name"] for d in filter_dishes_by_calories(make_dishes(), 320)]
    assert names == ["Овсяная каша", "Греческий салат"]


def test_sort_dishes():
    calories = [d["calories"] for d in sort_dishes(make_dishes())]
    assert calories == [250, 320, 560]
    assert sort_dishes(make_dishes(), by="name")[0]["name"] == \
        "Греческий салат"
