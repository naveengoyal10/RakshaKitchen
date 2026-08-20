import os

import django


def main():
    username = os.getenv("ADMIN_USERNAME", os.getenv("DJANGO_SUPERUSER_USERNAME", "")).strip()
    email = os.getenv("ADMIN_EMAIL", os.getenv("DJANGO_SUPERUSER_EMAIL", "")).strip()
    password = os.getenv("ADMIN_PASSWORD", os.getenv("DJANGO_SUPERUSER_PASSWORD", ""))
    if not all((username, email, password)):
        print("Admin bootstrap skipped: set ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD to enable it.")
        return

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    user, created = user_model.objects.get_or_create(username=username, defaults={"email": email})
    user.email = email
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    print(f"Admin user {'created' if created else 'updated'}: {username}")


if __name__ == "__main__":
    main()