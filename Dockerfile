ARG PYTHON_IMAGE=python:3.14-slim-bookworm@sha256:a9bee15510a364124aa24692899d269835683b883de42f7ebec8c293cf679ccb

FROM ${PYTHON_IMAGE} AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY requirements ./requirements
COPY src ./src
RUN python -m pip install \
      --constraint requirements/build.constraints.txt \
      pip==26.1.2 \
    && python -m pip download \
      --only-binary=:all: \
      --dest /wheels \
      pip==26.1.2 \
    && python -m pip wheel \
      --constraint requirements/runtime.constraints.txt \
      --wheel-dir /wheels \
      .

FROM ${PYTHON_IMAGE} AS runtime

ENV HOME=/tmp \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --home-dir /nonexistent \
      --shell /usr/sbin/nologin app

WORKDIR /app
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-index --find-links=/wheels pip==26.1.2 \
    && python -m pip install --no-index --find-links=/wheels msentraauth-flask-template \
    && rm -rf /wheels
COPY --chown=10001:10001 wsgi.py gunicorn.conf.py ./

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"

CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]
