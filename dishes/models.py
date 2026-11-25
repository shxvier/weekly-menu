from uuid import uuid4

from django.core.validators import MinValueValidator
from django.db import models, router, transaction
from django.db.models import Case, Value, When
from django.urls import reverse
from django.utils.text import slugify
from unidecode import unidecode

from dishes.validators import validate_image_size

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
    # Фотография блюда: файл хранится в MEDIA_ROOT/dishes/,
    # в базе данных – только путь к нему. Поле необязательное.
    image = models.ImageField(
        upload_to="dishes/",
        blank=True,
        null=True,
        validators=[validate_image_size],
        verbose_name="Фотография",
        help_text="JPG, PNG или WebP, не больше 2 МБ.",
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
        if self.slug:
            super().save(*args, **kwargs)
        elif self.pk is not None:
            self.slug = self.slug_for_pk()
            super().save(*args, **kwargs)
        else:
            using = kwargs.get("using") or router.db_for_write(
                type(self), instance=self,
            )
            previous_slug = self.slug
            previous_state = self._state.adding, self._state.db
            # Временный slug уникален и остаётся внутри транзакции.
            try:
                with transaction.atomic(using=using):
                    self.slug = f"new-{uuid4().hex}"
                    super().save(*args, **kwargs)
                    self.slug = self.slug_for_pk()
                    super().save(using=using, update_fields=["slug"])
            except Exception:
                self.pk = None
                self.slug = previous_slug
                self._state.adding, self._state.db = previous_state
                raise

    def slug_for_pk(self):
        base_slug = slugify(unidecode(self.name)) or "dish"
        suffix = f"-{self.pk}"
        max_length = self._meta.get_field("slug").max_length - len(suffix)
        return base_slug[:max_length].rstrip("-_") + suffix

    def get_absolute_url(self):
        """Адрес страницы блюда по именованному маршруту."""
        return reverse("dishes:detail", kwargs={"slug": self.slug})

    def fits_limit(self, max_calories):
        """Проверить, укладывается ли блюдо в лимит калорий."""
        return self.calories <= max_calories
