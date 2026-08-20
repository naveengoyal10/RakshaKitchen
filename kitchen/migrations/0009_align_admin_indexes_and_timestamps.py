from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0008_admin_content_and_order_management")]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="menuitemvariant",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
