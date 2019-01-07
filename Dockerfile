# Based on:
# https://www.caktusgroup.com/blog/2017/03/14/production-ready-dockerfile-your-python-django-app/

FROM python:3.7-alpine
ENV PYTHONUNBUFFERED 1

ENV APP_ENV=prod \
    APP_DIR=/code \
    DJANGO_PROJECT=storkive \
    # Semi-hack to get pipenv to use the desired directory.
    VIRTUAL_ENV=/venv

COPY Pipfile Pipfile.lock /

# Add mailcap for /etc/mime.types and tini for signal passing.
RUN apk add --no-cache \
  mailcap \
  tini

# Install build deps, then run `pipenv install`, then remove unneeded build deps all
# in a single step. Correct the path to your production requirements file, if needed.
RUN set -ex \
    && apk add --no-cache --virtual .build-deps \
            gcc \
            make \
            libc-dev \
            libffi-dev \
            libxml2-dev \
            libxslt-dev \
            musl-dev \
            linux-headers \
            pcre-dev \
            postgresql-dev \
    && pip install -U pip pipenv virtualenv \
    && virtualenv /venv \
    && LIBRARY_PATH=/lib:/usr/lib /bin/sh -c "pipenv install -v --deploy --clear" \
    && runDeps="$( \
            scanelf --needed --nobanner --recursive /venv \
                    | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
                    | sort -u \
                    | xargs -r apk info --installed \
                    | sort -u \
    )" \
    && apk add --virtual .python-rundeps $runDeps \
    && apk del .build-deps


RUN mkdir -p $APP_DIR
WORKDIR $APP_DIR

COPY . ./

# uWSGI will listen on this port
EXPOSE 8080

# Add any custom, static environment variables needed by Django or your settings file here:
ENV DJANGO_SETTINGS_MODULE=settings

# uWSGI configuration (customize as needed):
ENV UWSGI_VIRTUALENV=/venv \
    UWSGI_MODULE=$DJANGO_PROJECT.wsgi:application \
    UWSGI_STATIC_MAP="/static=/code/static" \
    UWSGI_MASTER=1 \
    UWSGI_WORKERS=2 \
    UWSGI_THREADS=8 \
    UWSGI_UID=1000 \
    UWSGI_GID=2000 \
    UWSGI_WSGI_ENV_BEHAVIOR=holy

# Call collectstatic (customize the following line with the minimal environment variables
# needed for manage.py to run):
RUN DATABASE_HOST=none /venv/bin/python manage.py collectstatic --no-input

# Start uWSGI
ENTRYPOINT ["/sbin/tini", "-v", "--"]
CMD ["/venv/bin/uwsgi", "--http", ":8080"]
