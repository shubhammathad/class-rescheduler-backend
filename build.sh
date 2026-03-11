#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install all dependencies (including psycopg2 and gunicorn)
pip install -r requirements.txt

# 2. Collect static files for the Admin panel styling
python manage.py collectstatic --no-input

# 3. Run database migrations to set up your Postgres tables
python manage.py migrate

# 4. Auto-create the Superuser using Environment Variables
if [ "$CREATE_SUPERUSER" ]; then
  python manage.py shell << END
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print("✅ Superuser created successfully.")
else:
    print("ℹ️ Superuser already exists. Skipping.")
END
fi