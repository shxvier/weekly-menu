from django.db import migrations, models
from django.db.models import Count


def keep_one_entry_per_slot(apps, schema_editor):
    MenuEntry = apps.get_model("menu", "MenuEntry")
    in_menu = MenuEntry.objects.using(schema_editor.connection.alias).filter(
        status__in=("active", "completed"),
    )
    slots = (
        in_menu.order_by()
        .values("dish_id", "user_id", "menu_date")
        .annotate(entry_count=Count("pk"))
        .filter(entry_count__gt=1)
        .values("dish_id", "user_id", "menu_date")
    )
    for slot in list(slots):
        entries = in_menu.filter(**slot)
        # Выполненная запись имеет приоритет, затем выбирается наименьший ID.
        keep = entries.order_by("-status", "pk").values_list("pk", flat=True)[0]
        entries.exclude(pk=keep).update(status="cancelled")


class Migration(migrations.Migration):
    dependencies = [
        ("menu", "0004_remove_menuentry_is_cancelled"),
    ]

    operations = [
        migrations.RunPython(keep_one_entry_per_slot, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="menuentry",
            constraint=models.UniqueConstraint(
                fields=("dish", "user", "menu_date"),
                condition=models.Q(status__in=("active", "completed")),
                name="menu_unique_live_dish_per_day",
                violation_error_message=(
                    "Это блюдо уже есть в меню пользователя на выбранную дату."
                ),
            ),
        ),
    ]
