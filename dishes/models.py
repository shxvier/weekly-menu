from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, Value, When
from django.urls import reverse
from django.utils.text import slugify
from unidecode import unidecode

# Порог «лёгкого» блюда, ккал на порцию.
LIGHT_DISH_MAX_CALORIES = 300

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
        help_text="Калорийность одной порции, целое число не меньше 1.",
    )
    # Англоязычный идентификатор для URL страницы блюда.
    slug = models.SlugField(
        max_length=220,
        unique=True,
        editable=False,
        verbose_name="URL-идентификатор",
    )
    # Признак лёгкого блюда вычисляет база данных по калорийности;
    # db_persist=True – значение хранится в столбце и пересчитывается
    # при изменении calories. Вручную не редактируется.
    is_light = models.GeneratedField(
        expression=Case(
            When(calories__lte=LIGHT_DISH_MAX_CALORIES, then=Value(True)),
            default=Value(False),
            output_field=models.BooleanField(),
        ),
        output_field=models.BooleanField(),
        db_persist=True,
        verbose_name="Лёгкое блюдо",
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

    def save(self, *args, **kwargs):
        """Сохранить блюдо; при первом сохранении сформировать slug.

        slug = транслитерация названия + id, например
        «Греческий салат» -> grecheskii-salat-3. Уже заданный slug не
        меняется, чтобы адрес страницы оставался постоянным.
        """
        if not self.slug:
            base_slug = slugify(unidecode(self.name)) or "dish"
            if self.pk:
                self.slug = f"{base_slug}-{self.pk}"
            else:
                # У нового объекта ещё нет id: сначала сохраняем его.
                # Временный slug нужен из-за ограничения unique.
                self.slug = f"{base_slug}-new"
                super().save(*args, **kwargs)
                self.slug = f"{base_slug}-{self.pk}"
                super().save(update_fields=["slug"])
                return
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Адрес страницы блюда по именованному маршруту."""
        return reverse("dishes:detail", kwargs={"slug": self.slug})

    def fits_limit(self, max_calories):
        """Проверить, укладывается ли блюдо в лимит калорий."""
        return self.calories <= max_calories
