from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0012_align_food_item_flags")]

    operations = [
        migrations.RemoveIndex(model_name="foodvariant", name="kitchen_variant_item_idx"),
        migrations.RenameField(model_name="foodvariant", old_name="is_available", new_name="active"),
        migrations.AddIndex(model_name="foodvariant", index=models.Index(fields=["food_item", "active", "display_order"], name="kitchen_variant_item_idx")),
    ]
