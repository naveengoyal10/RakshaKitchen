from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0010_add_whatsapp_order_details")]

    operations = [
        migrations.RemoveIndex(model_name="category", name="kitchen_cat_active_order_idx"),
        migrations.RemoveIndex(model_name="menuitemvariant", name="kitchen_variant_item_idx"),
        migrations.RenameModel(old_name="MenuItem", new_name="FoodItem"),
        migrations.RenameModel(old_name="MenuItemVariant", new_name="FoodVariant"),
        migrations.RenameField(model_name="foodvariant", old_name="menu_item", new_name="food_item"),
        migrations.RenameField(model_name="category", old_name="is_active", new_name="active"),
        migrations.AddField(
            model_name="category",
            name="image",
            field=models.ImageField(blank=True, upload_to="categories/"),
        ),
        migrations.AlterField(
            model_name="fooditem",
            name="category",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="food_items", to="kitchen.category"),
        ),
        migrations.AlterModelOptions(
            name="fooditem",
            options={"ordering": ["display_order", "name"]},
        ),
        migrations.AlterModelOptions(
            name="foodvariant",
            options={"ordering": ["display_order", "name"]},
        ),
        migrations.AddIndex(model_name="category", index=models.Index(fields=["active", "display_order"], name="kitchen_cat_active_order_idx")),
        migrations.AddIndex(model_name="foodvariant", index=models.Index(fields=["food_item", "is_available", "display_order"], name="kitchen_variant_item_idx")),
    ]
