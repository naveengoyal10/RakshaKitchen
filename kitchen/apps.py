import os

from django.apps import AppConfig


class KitchenConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "kitchen"

    def ready(self):
        if os.getenv("VERCEL"):
            from django.contrib.auth.signals import user_logged_in

            user_logged_in.disconnect(dispatch_uid="update_last_login")
