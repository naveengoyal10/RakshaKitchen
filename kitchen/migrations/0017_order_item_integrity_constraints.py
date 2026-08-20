from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0016_customer_inquiry")]

    operations = [
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.CheckConstraint(condition=models.Q(price__gte=0), name="kitchen_order_item_price_gte_zero"),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.CheckConstraint(condition=models.Q(subtotal__gte=0), name="kitchen_order_item_subtotal_gte_zero"),
        ),
    ]
