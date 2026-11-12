"""Корневая маршрутизация проекта: подключает маршруты приложений."""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("dishes/", include("dishes.urls")),
    path("menu/", include("menu.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]

handler404 = "homepage.views.page_not_found"
