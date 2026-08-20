from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0018_order_integrity_constraints")]

    operations = [
        migrations.AddField(
            model_name="websitesettings",
            name="hero_image",
            field=models.ImageField(blank=True, upload_to="site/"),
        ),
    ]
