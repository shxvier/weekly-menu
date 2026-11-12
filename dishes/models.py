from django.core.validators import MinValueValidator
from django.db import models

# Допустимые типы блюд: значение в базе – подпись в интерфейсе.
DISH_TYPE_CHOICES = [
    ("завтрак", "Завтрак"),
    ("обед", "Обед"),
    ("ужин", "Ужин"),
    ("перекус", "Перекус"),
]


class Dish(models.Model):
    """Блюдо, которое можно включить в меню."""

    # Название блюда.
    name = models.CharField(
        max_length=200,
        verbose_name="Название",
    )
    # Калорийность порции: положительное целое число.
    calories = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Калорийность, ккал",
    )
    # Тип блюда из фиксированного набора; по умолчанию – обед.
    dish_type = models.CharField(
        max_length=20,
        choices=DISH_TYPE_CHOICES,
        default="обед",
        verbose_name="Тип блюда",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Блюдо"
        verbose_name_plural = "Блюда"

    def __str__(self):
        return self.name

    def fits_limit(self, max_calories):
        """Проверить, укладывается ли блюдо в лимит калорий."""
        return self.calories <= max_calories
