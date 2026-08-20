from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0025_fooditem_base_option_name")]

    operations = [
        migrations.AlterField(
            model_name="fooditem",
            name="unit",
            field=models.CharField(choices=[("piece", "Piece"), ("gram", "Grams"), ("plate", "Plate")], default="piece", max_length=10),
        ),
        migrations.AlterField(
            model_name="foodvariant",
            name="unit",
            field=models.CharField(choices=[("piece", "Piece"), ("gram", "Grams"), ("plate", "Plate")], default="piece", max_length=10),
        ),
    ]