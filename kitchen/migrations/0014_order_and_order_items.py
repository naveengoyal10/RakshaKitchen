from django.db import migrations, models
import django.db.models.deletion
import uuid


def generate_order_number_default():
    return f"RK-{uuid.uuid4().hex[:10].upper()}"


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0013_align_food_variant_fields")]

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_number", models.CharField(default=generate_order_number_default, editable=False, max_length=20, unique=True)),
                ("customer_name", models.CharField(max_length=120)),
                ("mobile", models.CharField(max_length=30)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("address", models.TextField()),
                ("preferred_date", models.DateField(blank=True, null=True)),
                ("preferred_time", models.TimeField(blank=True, null=True)),
                ("order_type", models.CharField(choices=[("delivery", "Delivery"), ("pickup", "Pickup"), ("bulk", "Bulk / party")], default="delivery", max_length=20)),
                ("notes", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("new", "New"), ("confirmed", "Confirmed"), ("preparing", "Preparing"), ("ready", "Ready"), ("delivered", "Delivered"), ("cancelled", "Cancelled")], default="new", max_length=20)),
                ("total_amount", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField()),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("subtotal", models.DecimalField(decimal_places=2, max_digits=10)),
                ("food_item", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_items", to="kitchen.fooditem")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="kitchen.order")),
                ("variant", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="order_items", to="kitchen.foodvariant")),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.AddIndex(model_name="order", index=models.Index(fields=["status", "-created_at"], name="kitchen_order_new_status_idx")),
        migrations.AddConstraint(model_name="orderitem", constraint=models.CheckConstraint(condition=models.Q(quantity__gt=0), name="kitchen_order_item_quantity_gt_zero")),
    ]
