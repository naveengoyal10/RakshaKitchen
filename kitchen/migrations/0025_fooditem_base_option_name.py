from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0024_fooditem_unit_pricing")]

    operations = [
        migrations.AddField(
            model_name="fooditem",
            name="base_option_name",
            field=models.CharField(default="Standard", help_text="Name shown for the main item option", max_length=80),
        ),
    ]