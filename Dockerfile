# syntax=docker/dockerfile:1.7

ARG PYTHON_IMAGE=python:3.12.13-alpine3.22

FROM ${PYTHON_IMAGE} AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY app/requirements.txt ./requirements.txt

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --requirement requirements.txt

FROM ${PYTHON_IMAGE} AS runtime

ARG APP_UID=10001
ARG APP_GID=10001

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup --system --gid "${APP_GID}" app && \
    adduser --system --disabled-password --no-create-home --uid "${APP_UID}" --ingroup app app

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=${APP_UID}:${APP_GID} app/ /app/

USER ${APP_UID}:${APP_GID}
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2).read()"]

CMD ["gunicorn", "--bind=0.0.0.0:8080", "--workers=2", "--threads=4", "--timeout=30", "--worker-tmp-dir=/tmp", "--access-logfile=-", "--error-logfile=-", "app:app"]
