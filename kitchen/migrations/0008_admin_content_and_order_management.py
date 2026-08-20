from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0007_add_order_items_summary")]

    operations = [
        migrations.AddField(model_name="category", name="created_at", field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now)),
        migrations.AddField(model_name="category", name="updated_at", field=models.DateTimeField(auto_now=True)),
        migrations.AddField(model_name="menuitem", name="updated_at", field=models.DateTimeField(auto_now=True)),
        migrations.AddField(model_name="menuitemvariant", name="created_at", field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now)),
        migrations.AddField(model_name="menuitemvariant", name="updated_at", field=models.DateTimeField(auto_now=True)),
        migrations.AddField(model_name="orderinquiry", name="request_type", field=models.CharField(choices=[("order", "Order"), ("enquiry", "Enquiry"), ("bulk", "Bulk / party order")], default="enquiry", max_length=20)),
        migrations.AddField(model_name="orderinquiry", name="status", field=models.CharField(choices=[("new", "New"), ("in_progress", "In progress"), ("confirmed", "Confirmed"), ("completed", "Completed"), ("cancelled", "Cancelled")], default="new", max_length=20)),
        migrations.AddField(model_name="orderinquiry", name="updated_at", field=models.DateTimeField(auto_now=True)),
        migrations.CreateModel(
            name="Testimonial",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("customer_name", models.CharField(max_length=120)),
                ("quote", models.TextField()),
                ("customer_role", models.CharField(blank=True, max_length=120)),
                ("rating", models.PositiveSmallIntegerField(default=5)),
                ("is_published", models.BooleanField(default=True)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["display_order", "-created_at"]},
        ),
        migrations.CreateModel(
            name="WebsiteSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("business_name", models.CharField(default="Raksha Kitchen", max_length=120)),
                ("tagline", models.CharField(default="Home-style food, made with heart.", max_length=180)),
                ("phone", models.CharField(blank=True, max_length=30)),
                ("whatsapp_number", models.CharField(blank=True, max_length=30)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("address", models.TextField(blank=True)),
                ("instagram_url", models.URLField(blank=True)),
                ("facebook_url", models.URLField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Website settings", "verbose_name_plural": "Website settings"},
        ),
        migrations.AlterModelOptions(name="category", options={"ordering": ["display_order", "name"], "verbose_name_plural": "Categories"}),
        migrations.AlterModelOptions(name="menuitemvariant", options={"ordering": ["display_order", "name"]}),
        migrations.AlterModelOptions(name="orderinquiry", options={"ordering": ["-created_at"]}),
        migrations.AddIndex(model_name="category", index=models.Index(fields=["is_active", "display_order"], name="kitchen_cat_active_order_idx")),
        migrations.AddIndex(model_name="menuitem", index=models.Index(fields=["category", "is_available", "display_order"], name="kitchen_item_category_idx")),
        migrations.AddIndex(model_name="menuitem", index=models.Index(fields=["is_featured", "is_available"], name="kitchen_item_featured_idx")),
        migrations.AddIndex(model_name="menuitemvariant", index=models.Index(fields=["menu_item", "is_available", "display_order"], name="kitchen_variant_item_idx")),
        migrations.AddIndex(model_name="orderinquiry", index=models.Index(fields=["status", "-created_at"], name="kitchen_order_status_idx")),
        migrations.AddIndex(model_name="orderinquiry", index=models.Index(fields=["request_type", "-created_at"], name="kitchen_order_type_idx")),
        migrations.AddIndex(model_name="testimonial", index=models.Index(fields=["is_published", "display_order"], name="kitchen_test_published_idx")),
    ]
