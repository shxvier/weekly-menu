from django.contrib import admin

from menu.admin import MenuEntryInline
from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "goal", "daily_limit")
    list_display_links = ("name",)
    search_fields = ("name", "goal")
    ordering = ("name",)
    list_per_page = 20
    readonly_fields = ("id",)
    inlines = (MenuEntryInline,)
