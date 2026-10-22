import pytest

from models import User
from models.users import add_user, find_user, find_user_by_id


def test_user_creation_and_str():
    user = User(1, "Анна", "поддержание веса", 2000)
    assert (user.id, user.name, user.daily_limit) == (1, "Анна", 2000)
    assert "Анна" in str(user)
    assert "2000" in str(user)


def test_user_from_data():
    data = {"id": 2, "name": "Иван", "goal": "набор массы",
            "daily_limit": 2800}
    user = User.from_data(data)
    assert user.name == "Иван"
    assert user.goal == "набор массы"


def test_add_and_find_users():
    users: list = []
    anna = add_user(users, "Анна", "цель", 2000)
    add_user(users, "Иван", "цель", 2800)
    assert anna.id == 1 and len(users) == 2
    assert [u.name for u in find_user(users, "иван")] == ["Иван"]
    assert find_user_by_id(users, 2).name == "Иван"
    assert find_user_by_id(users, 9) is None


def test_add_user_rejects_bad_data():
    with pytest.raises(ValueError):
        add_user([], "", "цель", 2000)
    with pytest.raises(ValueError):
        add_user([], "Анна", "цель", 0)
