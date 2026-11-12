from django.contrib import admin
from django.db.models import Count, Q

from dishes.models import Dish
from menu.admin import MenuEntryInline


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "calories",
        "dish_type",
        "active_entries_count",
    )
    list_display_links = ("name",)
    # Калорийность можно править прямо в списке.
    list_editable = ("calories",)
    search_fields = ("name",)
    list_filter = ("dish_type",)
    ordering = ("name",)
    list_per_page = 20
    readonly_fields = ("id",)
    inlines = (MenuEntryInline,)

    def get_queryset(self, request):
        # Число активных записей считается одним запросом для всех строк.
        return super().get_queryset(request).annotate(
            active_entries=Count(
                "menu_entries",
                filter=Q(menu_entries__is_cancelled=False),
            ),
        )

    @admin.display(description="Активных записей", ordering="active_entries")
    def active_entries_count(self, obj):
        return obj.active_entries
