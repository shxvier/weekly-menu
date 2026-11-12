"""Регистронезависимый LIKE для кириллицы в SQLite.

Встроенный в SQLite оператор LIKE не различает регистр только для
латиницы: запрос name__icontains="овс" не найдёт «Овсяная каша».
При каждом подключении к SQLite регистрируется функция like(),
которая сравнивает строки без учёта регистра для любых букв Unicode.
Запросы ORM (icontains, contains и т. д.) при этом не меняются.
"""
import re
from functools import lru_cache


@lru_cache(maxsize=256)
def _like_to_regex(pattern, escape):
    """Преобразовать шаблон LIKE (% и _) в регулярное выражение."""
    parts = []
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if escape and char == escape and i + 1 < len(pattern):
            parts.append(re.escape(pattern[i + 1]))
            i += 2
            continue
        if char == "%":
            parts.append(".*")
        elif char == "_":
            parts.append(".")
        else:
            parts.append(re.escape(char))
        i += 1
    return re.compile("".join(parts), re.IGNORECASE | re.DOTALL)


def unicode_like(pattern, value, escape=None):
    """Реализация SQL «value LIKE pattern [ESCAPE escape]»."""
    if pattern is None or value is None:
        return None
    return _like_to_regex(pattern, escape).fullmatch(str(value)) is not None


def register_unicode_like(sender, connection, **kwargs):
    """Обработчик сигнала connection_created."""
    if connection.vendor != "sqlite":
        return
    raw = connection.connection
    raw.create_function("like", 2, unicode_like, deterministic=True)
    raw.create_function("like", 3, unicode_like, deterministic=True)
