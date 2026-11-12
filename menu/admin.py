from django.contrib import admin, messages

from menu.models import MenuEntry


class MenuEntryInline(admin.TabularInline):
    """Записи меню внутри карточки блюда или пользователя."""

    model = MenuEntry
    fields = ("menu_date", "dish", "user", "is_cancelled")
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
        "is_cancelled",
    )
    list_display_links = ("id",)
    # Поиск по полям связанных моделей.
    search_fields = ("dish__name", "user__name")
    list_filter = ("menu_date", "is_cancelled", "dish__dish_type", "user")
    ordering = ("-menu_date", "id")
    list_per_page = 20
    readonly_fields = ("id",)
    # Блюдо и пользователь загружаются одним запросом с JOIN.
    list_select_related = ("dish", "user")
    date_hierarchy = "menu_date"
    autocomplete_fields = ("dish", "user")
    actions = ("cancel_entries", "restore_entries")

    @admin.display(description="Ккал", ordering="dish__calories")
    def dish_calories(self, obj):
        return obj.dish.calories

    @admin.action(description="Отменить выбранные записи")
    def cancel_entries(self, request, queryset):
        count = 0
        for entry in queryset:
            entry.cancel()
            count += 1
        self.message_user(
            request, f"Отменено записей: {count}.", messages.SUCCESS,
        )

    @admin.action(description="Вернуть в активные")
    def restore_entries(self, request, queryset):
        updated = queryset.update(is_cancelled=False)
        self.message_user(
            request, f"Возвращено записей: {updated}.", messages.SUCCESS,
        )
