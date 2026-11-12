from django.urls import path

from . import views

app_name = "menu"

# Статические маршруты (create/, day/, statistics/) объявлены раньше
# маршрутов с параметром <int:entry_id>.
urlpatterns = [
    path("", views.menu_list, name="list"),
    path("create/", views.menu_create, name="create"),
    path("day/", views.day_menu, name="day"),
    path("statistics/", views.statistics, name="statistics"),
    path("<int:entry_id>/", views.menu_detail, name="detail"),
    path("<int:entry_id>/edit/", views.menu_update, name="update"),
    path("<int:entry_id>/cancel/", views.menu_cancel, name="cancel"),
]
