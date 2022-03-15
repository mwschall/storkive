#!/usr/bin/env sh
# https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/
# https://stackoverflow.com/a/3427931

if [ -n "$MANAGE_COLLECTCLEAR" ]; then
  python manage.py collectstatic --no-input --clear
elif [ -n "$MANAGE_COLLECTSTATIC" ]; then
  python manage.py collectstatic --no-input
fi

if [ "$DATABASE" = "postgres" ]; then
  echo "Waiting for postgres..."

  while ! nc -z "${SQL_HOST:-localhost}" "${SQL_PORT:-5432}"; do
    sleep 0.1
  done

  echo "PostgreSQL started"
fi

if [ -n "$MANAGE_FLUSH" ]; then
  python manage.py flush --no-input
fi

if [ -n "$MANAGE_MIGRATE" ]; then
  python manage.py migrate
fi

exec "$@"
