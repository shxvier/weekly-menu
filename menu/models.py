from django.db import models

from dishes.models import Dish
from users.models import User


class MenuEntry(models.Model):
    """Запись меню: блюдо, запланированное пользователю на дату."""

    # Блюдо записи. PROTECT запрещает удалить блюдо, пока оно
    # встречается в меню, – история меню сохраняется.
    dish = models.ForeignKey(
        Dish,
        on_delete=models.PROTECT,
        related_name="menu_entries",
        verbose_name="Блюдо",
    )
    # Пользователь, для которого запланировано блюдо.
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="menu_entries",
        verbose_name="Пользователь",
    )
    # Дата приёма пищи: DateField хранит дату, а не строку.
    menu_date = models.DateField(
        verbose_name="Дата",
    )
    # Отменённая запись остаётся в истории и не учитывается в меню.
    is_cancelled = models.BooleanField(
        default=False,
        verbose_name="Запись отменена",
    )

    class Meta:
        ordering = ["menu_date", "pk"]
        verbose_name = "Запись меню"
        verbose_name_plural = "Записи меню"

    def __str__(self):
        return f"{self.dish} — {self.menu_date} ({self.user})"

    def cancel(self):
        """Отменить запись и сохранить только изменённое поле."""
        self.is_cancelled = True
        self.save(update_fields=["is_cancelled"])
