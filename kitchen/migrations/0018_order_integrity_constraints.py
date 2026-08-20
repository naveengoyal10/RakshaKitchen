from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0017_order_item_integrity_constraints")]

    operations = [
        migrations.AddConstraint(
            model_name="foodvariant",
            constraint=models.CheckConstraint(condition=models.Q(price__gte=0), name="kitchen_variant_price_gte_zero"),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.CheckConstraint(condition=models.Q(total_amount__gte=0), name="kitchen_order_total_gte_zero"),
        ),
    ]
