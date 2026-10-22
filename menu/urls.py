from django.urls import path

from . import views

app_name = "menu"

urlpatterns = [
    path("", views.menu_list, name="list"),
    path("<int:entry_id>/", views.menu_detail, name="detail"),
    path("day/", views.day_menu, name="day"),
    path("statistics/", views.statistics, name="statistics"),
]
