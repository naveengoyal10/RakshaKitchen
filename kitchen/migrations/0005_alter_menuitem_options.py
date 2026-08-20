from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0004_configurable_categories_and_item_options")]

    operations = [
        migrations.AlterModelOptions(
            name="menuitem",
            options={"ordering": ["display_order", "name"]},
        ),
    ]
