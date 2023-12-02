VERSION 0.7
FROM alpine

python-requirements:
    # renovate: datasource=docker depName=python versioning=docker
    ARG PYTHON_VERSION=3.12
    FROM python:$PYTHON_VERSION
    WORKDIR /usr/src/app
    COPY requirements.txt .
    COPY setup.cfg .
    COPY setup.py .
    RUN pip install --no-cache-dir -r requirements.txt

python-dev-requirements:
    FROM +python-requirements
    WORKDIR /usr/src/app
    COPY requirements-dev.txt .
    RUN pip install --no-cache-dir -r requirements-dev.txt

pyright-image:
    # renovate: datasource=pypi depName=pyright
    ARG PYRIGHT_VERSION=1.1.338
    FROM +python-dev-requirements
    RUN pip install --no-cache-dir pyright==$PYRIGHT_VERSION
    RUN nodeenv /.cache/nodeenv
    ENV PYRIGHT_PYTHON_ENV_DIR=/.cache/nodeenv
    WORKDIR /usr/src/app
    COPY pyproject.toml .
    COPY --dir aiobrultech_serial .

pyright-validate:
    FROM +pyright-image
    COPY --dir scripts .
    COPY --dir tests .
    COPY --dir typings .
    RUN pyright

pyright-verify-types:
    FROM +pyright-image
    RUN pip install .
    RUN pyright --verifytypes aiobrultech_serial

pyright-verify-stubs:
    FROM +pyright-image
    COPY --dir typings git-typings
    RUN pyright --createstub serial_asyncio
    # If this fails, delete and regenerate with `pyright --createstub serial_asyncio`.
    RUN find typings -name "*.pyi" -type f -print \
        | awk '{print "git-"$1" "$1}' \
        | xargs -n 2 diff -U8 -p

renovate-validate:
    # renovate: datasource=docker depName=renovate/renovate versioning=docker
    ARG RENOVATE_VERSION=37
    FROM renovate/renovate:$RENOVATE_VERSION
    WORKDIR /usr/src/app
    COPY renovate.json .
    RUN renovate-config-validator

ruff-validate:
    FROM +python-dev-requirements
    WORKDIR /usr/src/app
    COPY pyproject.toml .
    COPY --dir aiobrultech_serial .
    COPY --dir scripts .
    COPY --dir tests .
    RUN ruff check . --diff

lint:
    BUILD +pyright-validate
    BUILD +pyright-verify-stubs
    BUILD +pyright-verify-types
    BUILD +renovate-validate
    BUILD +ruff-validate
