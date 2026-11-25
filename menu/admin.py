from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef
from django.forms import BaseInlineFormSet

from menu.models import TAKEN_ERROR, MenuEntry


class MenuEntryInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        slots = set()
        for form in self.forms:
            data = form.cleaned_data
            if (
                data.get("DELETE")
                or data.get("status") not in MenuEntry.IN_MENU_STATUSES
            ):
                continue
            entry = form.instance
            key = (entry.dish_id, entry.user_id, entry.menu_date)
            if key in slots or (
                form.has_changed()
                and MenuEntry.objects.slot_taken(*key, exclude_pk=entry.pk)
            ):
                raise ValidationError(TAKEN_ERROR)
            slots.add(key)


class MenuEntryInline(admin.TabularInline):
    """Записи меню внутри карточки блюда или пользователя."""

    model = MenuEntry
    formset = MenuEntryInlineFormSet
    fields = ("menu_date", "dish", "user", "status")
    extra = 0
    ordering = ("-menu_date",)
    autocomplete_fields = ("dish", "user")
    show_change_link = True


@admin.register(MenuEntry)
class MenuEntryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "menu_date",
        "dish",
        "dish_calories",
        "user",
        "status",
    )
    list_display_links = ("id",)
    # Поиск по полям связанных моделей.
    search_fields = ("dish__name", "user__name")
    list_filter = ("menu_date", "status", "dish__dish_type", "user")
    ordering = ("-menu_date", "id")
    list_per_page = 20
    readonly_fields = ("id",)
    # Блюдо и пользователь загружаются одним запросом с JOIN.
    list_select_related = ("dish", "user")
    date_hierarchy = "menu_date"
    autocomplete_fields = ("dish", "user")
    actions = ("cancel_entries", "complete_entries", "restore_entries")

    @admin.display(description="Ккал", ordering="dish__calories")
    def dish_calories(self, obj):
        return obj.dish.calories

    @admin.action(description="Отменить выбранные записи")
    def cancel_entries(self, request, queryset):
        count = queryset.in_menu().update(status=MenuEntry.Status.CANCELLED)
        self.message_user(
            request, f"Отменено записей: {count}.", messages.SUCCESS,
        )

    @admin.action(description="Отметить как выполненные")
    def complete_entries(self, request, queryset):
        self.set_in_menu_status(
            request, queryset, MenuEntry.Status.COMPLETED, "Выполнено",
        )

    @admin.action(description="Вернуть в запланированные")
    def restore_entries(self, request, queryset):
        self.set_in_menu_status(
            request, queryset, MenuEntry.Status.ACTIVE, "Возвращено",
        )

    def set_in_menu_status(self, request, queryset, status, message):
        updated = (
            queryset.in_menu().exclude(status=status).update(status=status)
        )
        occupied = MenuEntry.objects.in_menu().matching_slot(
            OuterRef("dish_id"), OuterRef("user_id"), OuterRef("menu_date"),
        )
        cancelled = queryset.cancelled()
        skipped = 0
        for pk in cancelled.order_by("pk").values_list("pk", flat=True):
            changed = cancelled.filter(~Exists(occupied), pk=pk).update(
                status=status,
            )
            updated += changed
            skipped += 1 - changed
        self.message_user(
            request, f"{message} записей: {updated}.", messages.SUCCESS,
        )
        if skipped:
            self.message_user(
                request,
                f"Пропущено записей с занятым блюдом на эту дату: {skipped}.",
                messages.WARNING,
            )
