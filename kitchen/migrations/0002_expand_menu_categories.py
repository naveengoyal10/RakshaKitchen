from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="menuitem",
            name="category",
            field=models.CharField(
                choices=[
                    ("meals", "Meals"),
                    ("snacks", "Snacks"),
                    ("sides", "Sides"),
                    ("sweets", "Sweets"),
                    ("party", "Party & catering"),
                ],
                default="meals",
                max_length=20,
            ),
        ),
    ]
