from django.db import migrations, models


def copy_vegetarian_flag(apps, schema_editor):
    FoodItem = apps.get_model("kitchen", "FoodItem")
    FoodItem.objects.filter(dietary_type="vegetarian").update(vegetarian=True)


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0011_rename_menu_models_and_expand_categories")]

    operations = [
        migrations.RemoveIndex(model_name="fooditem", name="kitchen_item_category_idx"),
        migrations.RemoveIndex(model_name="fooditem", name="kitchen_item_featured_idx"),
        migrations.AddField(
            model_name="fooditem",
            name="vegetarian",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(copy_vegetarian_flag, migrations.RunPython.noop),
        migrations.RemoveField(model_name="fooditem", name="dietary_type"),
        migrations.RenameField(model_name="fooditem", old_name="is_jain_available", new_name="jain_available"),
        migrations.RenameField(model_name="fooditem", old_name="is_featured", new_name="featured"),
        migrations.RenameField(model_name="fooditem", old_name="is_available", new_name="available"),
        migrations.AddIndex(model_name="fooditem", index=models.Index(fields=["category", "available", "display_order"], name="kitchen_item_category_idx")),
        migrations.AddIndex(model_name="fooditem", index=models.Index(fields=["featured", "available"], name="kitchen_item_featured_idx")),
    ]
