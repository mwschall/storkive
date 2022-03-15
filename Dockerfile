#########################################
# Base Image                            #
#########################################

ARG USE_PYTHON=3.9
ARG USE_IMAGE=alpine

FROM python:${USE_PYTHON}-${USE_IMAGE} as base-image

    # python
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    # prevents python from creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # paths
    # this is where our requirements + virtual environment will live
    APP_HOME="/code" \
    APP_VENV="/opt/.virtualenvs/app"

    # add gcloud/gsutil and our venv to the path
ENV PATH=$CLOUD_SDK_HOME/bin:$APP_VENV/bin:$PATH \
    # poetry really likes to create its own venv (for now)
    APP_POETRY="$APP_HOME/.venv"

# new hotness
RUN set -x && \
    apk -U upgrade && \
    pip install --no-cache-dir -U pip



#########################################
# Builder Image                         #
#########################################

FROM base-image as builder-image

    # pip
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    # poetry
    POETRY_HOME="/opt/poetry" \
    # make poetry create the virtual environment in the project's root
    # it gets named `.venv`
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # forgo interactive questions
    POETRY_NO_INTERACTION=1

    # add poetry to the path
ENV PATH=$POETRY_HOME/bin:$PATH

RUN set -x && \
    # install necessary development packages
    apk add --no-cache --virtual .build-deps \
        gcc \
        libc-dev \
        libffi-dev \
        libxml2-dev \
        libxslt-dev \
        linux-headers \
        make \
        musl-dev \
        pcre-dev \
        postgresql-dev && \
    # install poetry; respects $POETRY_HOME
    wget -qO- https://install.python-poetry.org | python -

# copy project requirement files here to ensure they will be cached
WORKDIR $APP_HOME
COPY poetry.lock pyproject.toml ./

RUN set -x && \
    # install app deps
    LIBRARY_PATH=/lib:/usr/lib poetry install --no-dev --no-ansi && \
    scanelf --needed --nobanner --recursive $APP_POETRY \
            | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
            | sort -u \
            | xargs -r apk info --installed \
            | sort -u \
    > $APP_POETRY/deps


#########################################
# Common Image                          #
#########################################

FROM base-image as common-image

# copy in our built venv
COPY --from=builder-image $APP_POETRY $APP_VENV

RUN set -x && \
    # use copied list because scanning here misses some dependencies
    apk add --no-cache --virtual .app-deps \
        $(cat $APP_VENV/deps) && \
    # add mailcap for /etc/mime.types file
    apk add --no-cache --virtual .storkive-deps \
        mailcap \
        tini

# make shell life easier
ENV PYTHONPATH=$APP_HOME \
    DJANGO_SETTINGS_MODULE=settings \
    DATABASE=${DATABASE:-postgres}

# multi-function entry point
COPY --chmod=755 docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]



#########################################
# Production Image                      #
#########################################

FROM common-image as production
ENV APP_ENV=prod

# copy our files
WORKDIR $APP_HOME
COPY . .

    # create a non-root system user to run as
RUN addgroup -S -g 1000 storkive && \
    adduser -S -u 1000 -G storkive -s /bin/false storkive

# uWSGI configuration (customize as needed):
# https://github.com/unbit/uwsgi/issues/1792
# https://www.reddit.com/r/Python/comments/4s40ge/understanding_uwsgi_threads_processes_and_gil/d56f3oo
ENV UWSGI_VIRTUALENV=$APP_VENV \
    UWSGI_MODULE=storkive.wsgi:application \
    UWSGI_STATIC_MAP="/static=$APP_HOME/static" \
    UWSGI_MASTER=1 \
    UWSGI_WORKERS=4 \
    UWSGI_HARAKIRI=20 \
    UWSGI_UID=storkive \
    UWSGI_GID=storkive \
    UWSGI_WSGI_ENV_BEHAVIOR=holy

# le port
EXPOSE 8080
# uWSGI expects this
STOPSIGNAL SIGINT
# Start uWSGI
CMD ["uwsgi", "--http-socket", "0.0.0.0:8080", "--http-keepalive"]
