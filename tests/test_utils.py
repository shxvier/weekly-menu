from datetime import date

from utils import (
    get_user_greeting,
    get_week_days,
    get_weekday_name,
    input_date,
    input_int,
    parse_date,
)


def test_parse_date_formats():
    assert parse_date("14.09.2026") == date(2026, 9, 14)
    assert parse_date("2026-09-14") == date(2026, 9, 14)
    assert parse_date("32.13.2026") is None
    assert parse_date("abc") is None


def test_week_helpers():
    week = get_week_days(date(2026, 9, 16))
    assert week[0] == date(2026, 9, 14)
    assert week[-1] == date(2026, 9, 20)
    assert get_weekday_name(week[0]) == "Понедельник"


def test_greeting():
    assert "Анна" in get_user_greeting("Анна", "цель")
    assert get_user_greeting("", "цель").startswith("Привет!")


def test_input_int_repeats_until_valid(monkeypatch):
    answers = iter(["abc", "-5", "7"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert input_int("? ", minimum=1) == 7


def test_input_date_repeats_until_valid(monkeypatch):
    answers = iter(["вчера", "15.09.2026"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert input_date("? ") == date(2026, 9, 15)
