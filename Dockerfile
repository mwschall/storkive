# Based on:
# https://www.caktusgroup.com/blog/2017/03/14/production-ready-dockerfile-your-python-django-app/

ARG USE_PYTHON=3.7

FROM python:${USE_PYTHON}-alpine as builder

RUN apk add --no-cache --virtual .build-deps \
        gcc \
        make \
        libc-dev \
        libffi-dev \
        libxml2-dev \
        libxslt-dev \
        musl-dev \
        linux-headers \
        pcre-dev \
        postgresql-dev

RUN pip install -U pip pipenv virtualenv

RUN virtualenv /venv

COPY Pipfile Pipfile.lock /

RUN LIBRARY_PATH=/lib:/usr/lib \
    VIRTUAL_ENV=/venv \
    PIPENV_VERBOSITY=-1 \
    /bin/sh -c "pipenv sync --clear"

# Collect and save list of necessary run dependencies.
RUN scanelf --needed --nobanner --recursive /venv \
            | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
            | sort -u \
            | xargs -r apk info --installed \
            | sort -u \
    > /venv/deps



FROM python:${USE_PYTHON}-alpine
ENV PYTHONUNBUFFERED 1

ENV APP_ENV=prod \
    APP_DIR=/code \
    DJANGO_PROJECT=storkive

COPY --from=builder /venv /venv/

# Add mailcap for /etc/mime.types and tini for signal passing.
RUN apk add --no-cache --virtual .storkive-deps \
  mailcap \
  tini

# Scanning the copied /venv directory misses some dependencies.
RUN apk add --no-cache --virtual .python-rundeps \
  $(cat /venv/deps)


RUN mkdir -p $APP_DIR
WORKDIR $APP_DIR

COPY . ./

# uWSGI will listen on this port
EXPOSE 8080

# Add any custom, static environment variables here:
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

# Call collectstatic (customize the following line with the minimal environment
# variables needed for manage.py to run):
RUN DATABASE_HOST=none /venv/bin/python manage.py collectstatic --no-input

# Start uWSGI
ENTRYPOINT ["/sbin/tini", "-v", "--"]
CMD ["/venv/bin/uwsgi", "--http", ":8080"]
