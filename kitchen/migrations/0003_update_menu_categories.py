from django.db import migrations, models


def rename_legacy_categories(apps, schema_editor):
    MenuItem = apps.get_model("kitchen", "MenuItem")
    MenuItem.objects.filter(category="meals").update(category="main_course")
    MenuItem.objects.filter(category="sides").update(category="snacks")
    MenuItem.objects.filter(category="party").update(category="party_orders")


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0002_expand_menu_categories")]

    operations = [
        migrations.RunPython(rename_legacy_categories, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="menuitem",
            name="category",
            field=models.CharField(
                choices=[
                    ("snacks", "Snacks"),
                    ("chaat", "Chaat"),
                    ("main_course", "Main Course"),
                    ("breakfast", "Breakfast"),
                    ("sweets", "Sweets"),
                    ("party_orders", "Party Orders"),
                    ("special_items", "Special Items"),
                ],
                default="main_course",
                max_length=20,
            ),
        ),
    ]
