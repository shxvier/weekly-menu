from django.db import models

from dishes.models import Dish
from users.models import User


class MenuEntryQuerySet(models.QuerySet):
    """Повторно используемые условия выборки записей меню."""

    def active(self):
        """Только запланированные записи."""
        return self.filter(status=self.model.Status.ACTIVE)

    def cancelled(self):
        """Только отменённые записи."""
        return self.filter(status=self.model.Status.CANCELLED)

    def completed(self):
        """Только выполненные (съеденные) записи."""
        return self.filter(status=self.model.Status.COMPLETED)

    def in_menu(self):
        """Записи, входящие в меню: все, кроме отменённых."""
        return self.exclude(status=self.model.Status.CANCELLED)

    def for_date(self, selected_date):
        """Записи на указанную дату (объект datetime.date)."""
        return self.filter(menu_date=selected_date)


class MenuEntryManager(models.Manager.from_queryset(MenuEntryQuerySet)):
    """Менеджер MenuEntry с методами MenuEntryQuerySet."""


class MenuEntry(models.Model):
    """Запись меню: блюдо, запланированное пользователю на дату.

    В меню дня (калорийность, запрет повторного блюда, статистика)
    учитываются запланированные и выполненные записи; отменённые –
    нет, но остаются в истории.
    """

    class Status(models.TextChoices):
        # Блюдо запланировано.
        ACTIVE = "active", "Запланировано"
        # Запись отменена: остаётся в истории, в меню не учитывается.
        CANCELLED = "cancelled", "Отменено"
        # Блюдо съедено: запись остаётся частью меню дня.
        COMPLETED = "completed", "Выполнено"

    # Статусы записей, входящих в меню.
    IN_MENU_STATUSES = (Status.ACTIVE, Status.COMPLETED)

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
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Статус",
    )

    objects = MenuEntryManager()

    class Meta:
        ordering = ["menu_date", "pk"]
        verbose_name = "Запись меню"
        verbose_name_plural = "Записи меню"

    def __str__(self):
        return f"{self.dish} — {self.menu_date} ({self.user})"

    def cancel(self):
        """Отменить запись и сохранить только изменённое поле."""
        self.status = self.Status.CANCELLED
        self.save(update_fields=["status"])
