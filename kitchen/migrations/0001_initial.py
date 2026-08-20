from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="MenuItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(unique=True)),
                ("description", models.TextField()),
                ("category", models.CharField(choices=[("mains", "Mains"), ("sides", "Sides"), ("sweets", "Sweets")], default="mains", max_length=20)),
                ("price", models.DecimalField(decimal_places=2, max_digits=8)),
                ("image", models.ImageField(blank=True, upload_to="menu/")),
                ("is_featured", models.BooleanField(default=False)),
                ("is_available", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["category", "name"]},
        ),
        migrations.CreateModel(
            name="OrderInquiry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("phone", models.CharField(max_length=30)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("event_date", models.DateField(blank=True, null=True)),
                ("servings", models.PositiveIntegerField(blank=True, null=True)),
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("is_contacted", models.BooleanField(default=False)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
