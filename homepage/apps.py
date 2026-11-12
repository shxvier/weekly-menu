from django.apps import AppConfig
from django.db.backends.signals import connection_created


class HomepageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "homepage"

    def ready(self):
        from homepage.sqlite_unicode import register_unicode_like

        connection_created.connect(register_unicode_like)
