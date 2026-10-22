import pytest

from models import Dish
from models.dishes import (
    add_dish,
    check_dish_calories,
    filter_dishes_by_calories,
    find_dish,
    find_dish_by_id,
    sort_dishes,
)


def make_dishes() -> list:
    dishes: list = []
    add_dish(dishes, "Овсяная каша", 320, "завтрак")
    add_dish(dishes, "Греческий салат", 250, "обед")
    add_dish(dishes, "Сёмга с рисом", 560, "ужин")
    return dishes


def test_dish_creation():
    dish = Dish(1, "Овсяная каша", 320, "завтрак")
    assert dish.id == 1
    assert dish.name == "Овсяная каша"
    assert dish.calories == 320
    assert dish.dish_type == "завтрак"


def test_dish_str():
    dish = Dish(1, "Овсяная каша", 320, "завтрак")
    assert str(dish) == "Овсяная каша, 320 ккал (завтрак)"


def test_dish_fits_limit():
    dish = Dish(1, "Каша", 320, "завтрак")
    assert dish.fits_limit(320)
    assert not dish.fits_limit(300)


def test_validate_calories_static_method():
    assert Dish.validate_calories(100)
    assert not Dish.validate_calories(0)
    assert not Dish.validate_calories(-5)


def test_dish_from_data():
    data = {"id": 7, "name": "Йогурт", "calories": 190,
            "dish_type": "перекус"}
    dish = Dish.from_data(data)
    assert (dish.id, dish.name, dish.calories) == (7, "Йогурт", 190)


def test_add_dish_returns_object_and_stores_it():
    dishes: list = []
    dish = add_dish(dishes, "Суп", 300, "обед")
    assert dishes == [dish]
    assert dish.id == 1


def test_add_dish_rejects_bad_data():
    with pytest.raises(ValueError):
        add_dish([], "  ", 100, "обед")
    with pytest.raises(ValueError):
        add_dish([], "Суп", 0, "обед")


def test_find_dish_and_find_by_id():
    dishes = make_dishes()
    assert [d.name for d in find_dish(dishes, "САЛАТ")] == ["Греческий салат"]
    assert find_dish_by_id(dishes, 3).name == "Сёмга с рисом"
    assert find_dish_by_id(dishes, 99) is None


def test_check_dish_calories_uses_method():
    dishes = make_dishes()
    assert check_dish_calories(dishes, 2, 300)
    assert not check_dish_calories(dishes, 3, 300)
    with pytest.raises(KeyError):
        check_dish_calories(dishes, 99, 300)


def test_filter_and_sort_dishes():
    dishes = make_dishes()
    selected = filter_dishes_by_calories(dishes, 320)
    assert [d.calories for d in sort_dishes(selected)] == [250, 320]
    assert sort_dishes(dishes, by="name")[0].name == "Греческий салат"
    assert sort_dishes(dishes, reverse=True)[0].calories == 560
