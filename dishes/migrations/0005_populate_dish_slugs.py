"""Заполнение slug у существующих блюд: транслитерация + id."""
from django.db import migrations
from django.utils.text import slugify
from unidecode import unidecode


def populate_dish_slugs(apps, schema_editor):
    # Историческая модель Dish на момент этой миграции.
    Dish = apps.get_model("dishes", "Dish")
    for dish in Dish.objects.all().order_by("pk"):
        base_slug = slugify(unidecode(dish.name)) or "dish"
        # id делает slug уникальным даже для одинаковых названий.
        dish.slug = f"{base_slug}-{dish.pk}"
        dish.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("dishes", "0004_dish_slug"),
    ]

    operations = [
        migrations.RunPython(populate_dish_slugs, migrations.RunPython.noop),
    ]
