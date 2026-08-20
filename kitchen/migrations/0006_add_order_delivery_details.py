from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0005_alter_menuitem_options")]

    operations = [
        migrations.AddField(
            model_name="orderinquiry",
            name="address",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="orderinquiry",
            name="preferred_time",
            field=models.TimeField(blank=True, null=True),
        ),
    ]
