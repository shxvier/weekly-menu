from django.contrib import admin
from django.db.models import Count, Q

from dishes.models import Dish
from menu.admin import MenuEntryInline
from menu.models import MenuEntry


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "calories",
        "dish_type",
        "entries_in_menu",
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
        # Число записей в меню считается одним запросом для всех строк.
        return super().get_queryset(request).annotate(
            in_menu_count=Count(
                "menu_entries",
                filter=Q(
                    menu_entries__status__in=MenuEntry.IN_MENU_STATUSES,
                ),
            ),
        )

    @admin.display(description="Записей в меню", ordering="in_menu_count")
    def entries_in_menu(self, obj):
        return obj.in_menu_count
