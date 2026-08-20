from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("kitchen", "0015_alter_order_order_number")]

    operations = [
        migrations.CreateModel(
            name="CustomerInquiry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("mobile", models.CharField(max_length=30)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("event_type", models.CharField(choices=[("birthday", "Birthday party"), ("house_party", "House party"), ("office", "Office event"), ("society", "Society event"), ("family", "Family function"), ("festival", "Festival"), ("catering", "Small catering requirement")], max_length=30)),
                ("event_date", models.DateField()),
                ("number_of_people", models.PositiveIntegerField()),
                ("food_requirements", models.TextField()),
                ("budget", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("address", models.TextField()),
                ("additional_notes", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("new", "New"), ("contacted", "Contacted"), ("quoted", "Quoted"), ("confirmed", "Confirmed"), ("closed", "Closed")], default="new", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(model_name="customerinquiry", index=models.Index(fields=["status", "-created_at"], name="kitchen_inquiry_status_idx")),
        migrations.AddIndex(model_name="customerinquiry", index=models.Index(fields=["event_type", "event_date"], name="kitchen_inquiry_event_idx")),
    ]
