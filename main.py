from datetime import date

# --- Данные пользователя ---
user_name = "Анна"
user_goal = "поддержание веса"

# --- Данные блюда ---
dish_name = "Овсяная каша с ягодами"
dish_calories = 320
dish_type = "завтрак"

# --- Данные дня ---
day_name = "Понедельник"
day_date = date(2026, 9, 14)
planned_dish = ""          # пока пусто
max_calories_per_day = 2000


def get_user_greeting(name: str, goal: str) -> str:
    """Формирует приветствие пользователя."""
    if not name:
        return "Привет! Давай составим меню на неделю."
    return f"Привет, {name}! Цель: {goal}. Составим меню на неделю."


def add_dish_to_day(current_dish: str, new_dish: str) -> str:
    """Добавляет блюдо в день, если он ещё пуст."""
    if current_dish == "":
        return new_dish
    return f"{current_dish}, {new_dish}"


def check_day_calories(calories: int, limit: int) -> str:
    """Проверяет, укладывается ли день в лимит калорий."""
    if calories > limit:
        return f"Превышение лимита на {calories - limit} ккал"
    return f"В пределах нормы (осталось {limit - calories} ккал)"


def format_menu_line(day: str, dish: str, calories: int) -> str:
    """Формирует строку меню для вывода."""
    if dish == "":
        return f"{day}: блюдо не выбрано"
    return f"{day}: {dish} — {calories} ккал"


def main() -> None:
    print(get_user_greeting(user_name, user_goal))
    print("-" * 40)

    # Планируем блюдо на день
    planned = add_dish_to_day(planned_dish, dish_name)
    print(f"Блюдо добавлено: {planned}")

    # Проверяем калорийность
    print(check_day_calories(dish_calories, max_calories_per_day))

    # Выводим строку меню
    print(format_menu_line(day_name, planned, dish_calories))
    print(f"Дата: {day_date}")
    print(f"Тип блюда: {dish_type}")


if __name__ == "__main__":
    main()
