from django.urls import path

from . import views

app_name = "dishes"

# create/ объявлен раньше <slug:slug>/, иначе адрес попал бы
# в маршрут карточки блюда.
urlpatterns = [
    path("", views.dish_list, name="list"),
    path("create/", views.dish_create, name="create"),
    path("<slug:slug>/", views.dish_detail, name="detail"),
    path("<slug:slug>/edit/", views.dish_update, name="update"),
]
