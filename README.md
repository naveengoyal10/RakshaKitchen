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

Set `DATABASE_URL` to a PostgreSQL URL in production, for example `postgresql://user:password@host:5432/raksha_kitchen`.

## Vercel deployment

Configure these Vercel project environment variables for Production before redeploying:

- `DJANGO_SECRET_KEY`: a long random secret
- `DJANGO_DEBUG`: `False`
- `DJANGO_ALLOWED_HOSTS`: your custom domain, if you use one
- `DJANGO_CSRF_TRUSTED_ORIGINS`: your custom domain as an HTTPS URL, if you use one
- `DATABASE_URL`: a hosted PostgreSQL connection URL

The Vercel build runs `collectstatic` and applies migrations. Do not use the local SQLite database for production because Vercel's filesystem is temporary.

## Production security

Set `DJANGO_DEBUG=False`, provide a unique `DJANGO_SECRET_KEY`, configure `DJANGO_ALLOWED_HOSTS`, and set `DJANGO_CSRF_TRUSTED_ORIGINS` to HTTPS origins only. Keep `.env`, database files, uploaded media, and generated static files outside version control. Run `py manage.py check --deploy` before deployment and serve the site behind HTTPS.
