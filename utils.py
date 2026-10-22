"""Вспомогательные функции: приветствие, работа с датами и ввод."""
from datetime import date, datetime, timedelta
from typing import Optional

WEEKDAY_NAMES = (
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
)
DATE_FORMATS = ("%d.%m.%Y", "%Y-%m-%d")


def get_user_greeting(name: str, goal: str) -> str:
    """Формирует приветствие пользователя."""
    if not name:
        return "Привет! Давай составим меню на неделю."
    return f"Привет, {name}! Цель: {goal}. Составим меню на неделю."


def parse_date(text: str) -> Optional[date]:
    """Преобразовать строку (ДД.ММ.ГГГГ или ГГГГ-ММ-ДД) в дату.

    Возвращает None, если строку не удалось разобрать.
    """
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(text.strip(), date_format).date()
        except ValueError:
            continue
    return None


def get_weekday_name(day: date) -> str:
    """Вернуть название дня недели по-русски."""
    return WEEKDAY_NAMES[day.weekday()]


def get_week_days(day: date) -> list[date]:
    """Вернуть семь дат недели (с понедельника), в которую входит day."""
    monday = day - timedelta(days=day.weekday())
    return [monday + timedelta(days=shift) for shift in range(7)]


def input_int(prompt: str, minimum: Optional[int] = None) -> int:
    """Запросить целое число; при ошибке ввода повторить запрос."""
    while True:
        text = input(prompt)
        try:
            value = int(text)
        except ValueError:
            print("Нужно ввести целое число.")
            continue
        if minimum is not None and value < minimum:
            print(f"Число должно быть не меньше {minimum}.")
            continue
        return value


def input_date(prompt: str) -> date:
    """Запросить дату; при неверном формате повторить запрос."""
    while True:
        parsed = parse_date(input(prompt))
        if parsed is not None:
            return parsed
        print("Неверная дата. Формат: ДД.ММ.ГГГГ, например 14.09.2026.")
