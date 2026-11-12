"""Перенос признака is_cancelled в поле status.

Отменённые записи получают статус "cancelled", остальные – "active".
Статус "completed" по дате не присваивается: это отдельное правило.
"""
from django.db import migrations


def migrate_menu_statuses(apps, schema_editor):
    # Историческая модель – состояние на момент этой миграции.
    MenuEntry = apps.get_model("menu", "MenuEntry")
    MenuEntry.objects.filter(is_cancelled=True).update(status="cancelled")
    MenuEntry.objects.filter(is_cancelled=False).update(status="active")


def reverse_menu_statuses(apps, schema_editor):
    MenuEntry = apps.get_model("menu", "MenuEntry")
    MenuEntry.objects.filter(status="cancelled").update(is_cancelled=True)
    MenuEntry.objects.exclude(status="cancelled").update(is_cancelled=False)


class Migration(migrations.Migration):

    dependencies = [
        ("menu", "0002_menuentry_status"),
    ]

    operations = [
        migrations.RunPython(migrate_menu_statuses, reverse_menu_statuses),
    ]
