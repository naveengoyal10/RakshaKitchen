from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0009_align_admin_indexes_and_timestamps")]

    operations = [
        migrations.AddField(
            model_name="orderinquiry",
            name="fulfillment_method",
            field=models.CharField(choices=[("delivery", "Delivery"), ("pickup", "Pickup")], default="delivery", max_length=20),
        ),
        migrations.AddField(
            model_name="orderinquiry",
            name="estimated_total",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
