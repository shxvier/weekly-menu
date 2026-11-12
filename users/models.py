from django.core.validators import MinValueValidator
from django.db import models


class User(models.Model):
    """Пользователь, для которого составляется меню.

    Это пользователь предметной области, а не встроенная модель
    аутентификации Django (django.contrib.auth.models.User).
    """

    # Имя пользователя.
    name = models.CharField(
        max_length=100,
        verbose_name="Имя",
    )
    # Цель питания необязательна: blank=True разрешает пустое значение
    # в формах, для строк Django хранит пустую строку, а не NULL.
    goal = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Цель",
    )
    # Дневной лимит калорий: целое число не меньше 1.
    daily_limit = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Дневной лимит, ккал",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.name
