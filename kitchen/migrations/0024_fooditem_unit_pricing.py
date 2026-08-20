from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0023_foodvariant_unit_pricing")]

    operations = [
        migrations.AddField(
            model_name="fooditem",
            name="unit_quantity",
            field=models.PositiveIntegerField(default=1, help_text="Number of pieces or grams included at this price"),
        ),
        migrations.AddField(
            model_name="fooditem",
            name="unit",
            field=models.CharField(choices=[("piece", "Piece"), ("gram", "Grams")], default="piece", max_length=10),
        ),
    ]