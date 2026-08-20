from django.db import migrations


def update_whatsapp_number(apps, schema_editor):
    website_settings = apps.get_model("kitchen", "WebsiteSettings")
    website_settings.objects.update(whatsapp_number="919305126262")


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0020_update_contact_details")]

    operations = [migrations.RunPython(update_whatsapp_number, migrations.RunPython.noop)]