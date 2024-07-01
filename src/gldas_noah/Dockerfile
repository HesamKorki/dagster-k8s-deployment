FROM python:3.11-slim

ARG DAGSTER_VERSION

RUN pip install -U uv
RUN python -m uv pip install \
    dagster==${DAGSTER_VERSION} \
    dagster-postgres \
    dagster-aws \
    dagster-k8s \
    dagster-celery[flower,redis,kubernetes] \
    dagster-celery-k8s


WORKDIR /app
COPY . /app

RUN python -m uv pip install -e ".[dev]"