from django.db import migrations, models

from kitchen.models import generate_order_number


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0014_order_and_order_items")]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="order_number",
            field=models.CharField(default=generate_order_number, editable=False, max_length=20, unique=True),
        ),
    ]
