from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0006_add_order_delivery_details")]

    operations = [
        migrations.AddField(
            model_name="orderinquiry",
            name="items_summary",
            field=models.TextField(blank=True),
        ),
    ]
