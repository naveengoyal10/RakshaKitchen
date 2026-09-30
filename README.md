# Raksha Kitchen

A production-minded Django website for a home-style food business. The storefront is original and uses the reference site only for broad business functionality.

## Local setup

1. Install Python 3.12+ and create an environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and update the secret key.
3. Run migrations and create an admin account:
   ```powershell
   py manage.py migrate
   py manage.py createsuperuser
   py manage.py runserver
   ```
4. Visit `http://127.0.0.1:8000/` and manage menu items at `/admin/`.

The storefront cart uses the existing `FoodItem`/`FoodVariant` catalog and Django session, with browser storage as a convenience. Checkout reloads current product/variant prices from the database, checks availability and admin-configured minimum quantities, and stores order-line price/name snapshots. An order is committed before email is attempted; mail failures are recorded and can be retried from the Django Admin Orders list using **Retry unsent customer/admin order emails**.

For local email testing, `DEBUG=True` defaults to `django.core.mail.backends.console.EmailBackend`, which prints messages to the development server console. To test actual delivery, configure the SMTP variables below. Email delivery requires a working SMTP account/provider; without it, the order is still saved and the failed email status is visible in Admin.

New/updated environment variables for checkout mail:

- `ADMIN_ORDER_EMAIL`: destination for new order alerts (required to deliver admin notifications)
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`: SMTP server settings
- `EMAIL_USE_TLS`: use STARTTLS (default `True`)
- `EMAIL_USE_SSL`: use implicit TLS (default `False`; do not enable together with TLS)
- `EMAIL_TIMEOUT`: SMTP connection timeout in seconds (default `10`)
- `DEFAULT_FROM_EMAIL`: verified sender/from address (defaults to `EMAIL_HOST_USER`, then `orders@rakshakitchen.in`)
- `RAKSHA_PHONE`, `RAKSHA_EMAIL`: business contact shown in receipts (existing storefront variables)

Set SMTP credentials and `ADMIN_ORDER_EMAIL` as environment variables in Vercel Project Settings; do not commit credentials to `.env` or source control. Redeploy after changing environment variables. Configure a valid sender address with the provider. The Vercel build already applies migrations; locally run `py manage.py migrate` before using the updated checkout. To set a product minimum, open its Food Item or Food Variant in Django Admin and set **Minimum quantity** (defaults to 1).

Run checkout and notification tests with `py manage.py test kitchen`. The tests use Django’s in-memory email backend and do not send real mail.

Set `DATABASE_URL` to a PostgreSQL URL in production, for example `postgresql://user:password@host:5432/raksha_kitchen`.

## Vercel deployment

Configure these Vercel project environment variables for Production before redeploying:

- `DJANGO_SECRET_KEY`: a long random secret
- `DJANGO_DEBUG`: `False`
- `DJANGO_ALLOWED_HOSTS`: your custom domain, if you use one
- `DJANGO_CSRF_TRUSTED_ORIGINS`: your custom domain as an HTTPS URL, if you use one
- `RAKSHA_SITE_URL`: your deployed site URL, including `https://`
- `DATABASE_URL` or `POSTGRES_URL`: a hosted PostgreSQL connection URL (required on Vercel). Neon `PGHOST`, `PGUSER`, `PGPASSWORD`, and `PGDATABASE` variables are also supported.
- `RAKSHA_PHONE`: `+91 93051 26262`
- `RAKSHA_EMAIL`: `raksha.shady@gmail.com`
- `RAKSHA_WHATSAPP`: `9305126262`
- `CLOUDINARY_URL`: Cloudinary connection URL for persistent uploaded images
- `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`: set all three to provision the Django admin account during the build

After adding or changing these variables, create a new deployment. The build log must contain `Admin user created` or `Admin user updated`; changing an environment variable does not modify an already completed deployment.

The Vercel build runs `collectstatic` and applies migrations, including creation of the Website Settings record used for the hero image and contact details. Vercel uses signed-cookie sessions for admin login, but `DATABASE_URL` must still point to hosted PostgreSQL because menu, order, and admin data cannot be stored reliably in local SQLite on Vercel. Set `CLOUDINARY_URL` to persist category and menu images.

## Production security

Set `DJANGO_DEBUG=False`, provide a unique `DJANGO_SECRET_KEY`, configure `DJANGO_ALLOWED_HOSTS`, and set `DJANGO_CSRF_TRUSTED_ORIGINS` to HTTPS origins only. Keep `.env`, database files, uploaded media, and generated static files outside version control. Run `py manage.py check --deploy` before deployment and serve the site behind HTTPS.
