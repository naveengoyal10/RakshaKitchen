from django.db import migrations


def update_contact_details(apps, schema_editor):
    website_settings = apps.get_model("kitchen", "WebsiteSettings")
    website_settings.objects.update(
        phone="+91 93051 26262",
        whatsapp_number="9305126262",
        email="raksha.shady@gmail.com",
    )


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0019_add_hero_image_to_settings")]

    operations = [migrations.RunPython(update_contact_details, migrations.RunPython.noop)]