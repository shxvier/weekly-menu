"""Класс User и функции обработки коллекции пользователей."""
from typing import List, Optional


class User:
    """Пользователь, для которого составляется меню."""

    def __init__(
        self,
        user_id: int,
        name: str,
        goal: str,
        daily_limit: int,
    ) -> None:
        """Создать объект пользователя."""
        self.id = user_id
        self.name = name
        self.goal = goal
        self.daily_limit = daily_limit

    @classmethod
    def from_data(cls, data: dict) -> "User":
        """Создать пользователя из словаря данных (например, из JSON)."""
        return cls(
            user_id=data["id"],
            name=data["name"],
            goal=data["goal"],
            daily_limit=data["daily_limit"],
        )

    def __str__(self) -> str:
        """Вернуть строковое представление пользователя."""
        return (
            f"{self.name} (цель: {self.goal}, "
            f"лимит {self.daily_limit} ккал в день)"
        )


def add_user(
    users: List[User],
    name: str,
    goal: str,
    daily_limit: int,
) -> User:
    """Создать пользователя, добавить в коллекцию и вернуть его."""
    name = name.strip()
    if not name:
        raise ValueError("Имя пользователя не может быть пустым")
    if daily_limit <= 0:
        raise ValueError("Лимит калорий должен быть положительным")
    user = User(
        max((item.id for item in users), default=0) + 1,
        name,
        goal.strip(),
        daily_limit,
    )
    users.append(user)
    return user


def find_user_by_id(users: List[User], user_id: int) -> Optional[User]:
    """Найти пользователя по идентификатору."""
    for user in users:
        if user.id == user_id:
            return user
    return None


def find_user(users: List[User], query: str) -> List[User]:
    """Найти пользователей по подстроке имени (без учёта регистра)."""
    query = query.strip().casefold()
    return [user for user in users if query in user.name.casefold()]


def show_users(users: List[User]) -> None:
    """Вывести список пользователей."""
    if not users:
        print("Пользователи не найдены.")
        return
    for user in users:
        print(f"{user.id:>3}. {user}")
