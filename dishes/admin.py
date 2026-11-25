from django.contrib import admin
from django.db.models import Count, ImageField, Q
from django.utils.html import format_html

from dishes.forms import DishPhotoField
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
        "is_light",
        "has_image",
        "entries_in_menu",
        "site_link",
    )
    list_display_links = ("name",)
    # Калорийность можно править прямо в списке.
    list_editable = ("calories",)
    search_fields = ("name",)
    list_filter = ("dish_type", "is_light")
    ordering = ("name",)
    list_per_page = 20
    readonly_fields = ("id", "slug", "is_light", "image_preview")
    formfield_overrides = {ImageField: {"form_class": DishPhotoField}}
    inlines = (MenuEntryInline,)
    # Ссылка «Смотреть на сайте» строится через get_absolute_url().
    view_on_site = True

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

    @admin.display(description="Страница на сайте")
    def site_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank">Открыть</a>',
            obj.get_absolute_url(),
        )

    @admin.display(description="Фото", boolean=True)
    def has_image(self, obj):
        return bool(obj.image)

    @admin.display(description="Текущая фотография")
    def image_preview(self, obj):
        if not obj.image:
            return "Фотография не загружена"
        return format_html(
            '<img src="{}" alt="" style="max-height: 160px;">',
            obj.image.url,
        )
