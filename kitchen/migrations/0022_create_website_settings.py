from django.db import migrations


def create_website_settings(apps, schema_editor):
    website_settings = apps.get_model("kitchen", "WebsiteSettings")
    website_settings.objects.get_or_create(
        id=1,
        defaults={
            "business_name": "Raksha Kitchen",
            "tagline": "Home-style food, made with heart.",
            "phone": "+91 93051 26262",
            "whatsapp_number": "919305126262",
            "email": "raksha.shady@gmail.com",
        },
    )


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0021_update_whatsapp_country_code")]

    operations = [migrations.RunPython(create_website_settings, migrations.RunPython.noop)]