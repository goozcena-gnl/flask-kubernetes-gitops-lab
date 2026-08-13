# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e

FROM python:3.12.13-alpine3.23@sha256:601d3d3797e90e2534782e69c85fafb7971b43f24c7b1b079b7e48dd435e458d AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY app/requirements.lock ./requirements.lock

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install \
      --no-cache-dir \
      --only-binary=:all: \
      --require-hashes \
      --requirement requirements.lock

FROM python:3.12.13-alpine3.23@sha256:601d3d3797e90e2534782e69c85fafb7971b43f24c7b1b079b7e48dd435e458d AS runtime

ARG APP_UID=10001
ARG APP_GID=10001

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup --system --gid "${APP_GID}" app && \
    adduser --system --disabled-password --no-create-home --uid "${APP_UID}" --ingroup app app

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=${APP_UID}:${APP_GID} app/__init__.py app/app.py /app/

USER ${APP_UID}:${APP_GID}
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2).read()"]

CMD ["gunicorn", "--bind=0.0.0.0:8080", "--workers=2", "--threads=4", "--timeout=30", "--worker-tmp-dir=/tmp", "--no-control-socket", "--access-logfile=-", "--error-logfile=-", "app:app"]
