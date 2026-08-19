# syntax=docker/dockerfile:1
# Multi-stage build: wheels are compiled in the builder, the runtime image
# carries only the installed package and runs as a non-root user.
FROM python:3.11-slim AS builder

WORKDIR /build

COPY pyproject.toml README.md ./
COPY clearglassinc_sdk ./clearglassinc_sdk

RUN pip install --no-cache-dir --upgrade pip build \
    && pip wheel --no-cache-dir --wheel-dir /wheels ".[server,all]"


FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    CLEARGLASS_SESSION_DIR=/data/sessions

RUN useradd --create-home --uid 10001 clearglass \
    && mkdir -p /data/sessions \
    && chown -R clearglass:clearglass /data

WORKDIR /app

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels \
        "clearglassinc-sdk[server,all]" \
    && rm -rf /wheels

USER clearglass

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status==200 else 1)"

CMD ["python", "-m", "clearglassinc_sdk.server"]
