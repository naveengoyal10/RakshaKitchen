from django.db import migrations, models
import django.db.models.deletion


CATEGORY_SEEDS = [
    ("Snacks", "snacks", "Little bites for chai time, sharing, or late-night cravings.", 1),
    ("Chaat", "chaat", "Bright, tangy, crunchy favourites made to order.", 2),
    ("Main Course", "main-course", "Comforting, generous dishes ready to make dinner easy.", 3),
    ("Breakfast", "breakfast", "A warm start for slow mornings and busy days.", 4),
    ("Sweets", "sweets", "Thoughtful treats for finishing a meal on a happy note.", 5),
    ("Party Orders", "party-orders", "Beautiful spreads for birthdays, offices, and big tables.", 6),
    ("Special Items", "special-items", "Seasonal favourites and limited treats worth seeking out.", 7),
]


def create_categories_and_move_items(apps, schema_editor):
    Category = apps.get_model("kitchen", "Category")
    MenuItem = apps.get_model("kitchen", "MenuItem")
    categories = {}
    for name, slug, description, display_order in CATEGORY_SEEDS:
        category = Category.objects.create(
            name=name,
            slug=slug,
            description=description,
            display_order=display_order,
        )
        categories[slug] = category

    legacy_map = {
        "snacks": "snacks",
        "chaat": "chaat",
        "main_course": "main-course",
        "breakfast": "breakfast",
        "sweets": "sweets",
        "party_orders": "party-orders",
        "special_items": "special-items",
        "meals": "main-course",
        "sides": "snacks",
        "party": "party-orders",
        "mains": "main-course",
    }
    for item in MenuItem.objects.all():
        item.category_id = categories[legacy_map.get(item.legacy_category, "main-course")].id
        item.save(update_fields=["category"])


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0003_update_menu_categories")]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80)),
                ("slug", models.SlugField(unique=True)),
                ("description", models.CharField(blank=True, max_length=180)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["display_order", "name"], "verbose_name_plural": "Categories"},
        ),
        migrations.CreateModel(
            name="MenuItemVariant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="For example: Half, Full, 250 g, or 1 kg", max_length=80)),
                ("price", models.DecimalField(decimal_places=2, max_digits=8)),
                ("is_available", models.BooleanField(default=True)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("menu_item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="variants", to="kitchen.menuitem")),
            ],
            options={"ordering": ["display_order", "name"]},
        ),
        migrations.RenameField(model_name="menuitem", old_name="category", new_name="legacy_category"),
        migrations.AddField(
            model_name="menuitem",
            name="category",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="menu_items", to="kitchen.category"),
        ),
        migrations.AddField(
            model_name="menuitem",
            name="dietary_type",
            field=models.CharField(choices=[("vegetarian", "Vegetarian"), ("non_vegetarian", "Non-vegetarian"), ("not_specified", "Not specified")], default="not_specified", max_length=20),
        ),
        migrations.AddField(model_name="menuitem", name="is_jain_available", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="menuitem", name="display_order", field=models.PositiveIntegerField(default=0)),
        migrations.RunPython(create_categories_and_move_items, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="menuitem",
            name="category",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="menu_items", to="kitchen.category"),
        ),
        migrations.RemoveField(model_name="menuitem", name="legacy_category"),
    ]
