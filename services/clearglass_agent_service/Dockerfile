FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV CLEARGLASS_DISABLE_DOCS=false

WORKDIR /app

COPY services/clearglass_agent_service/requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip cache purge

COPY services/clearglass_agent_service ./clearglass_agent_service

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin clearglass \
    && chown -R clearglass:clearglass /app
USER clearglass

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT','8080'), timeout=3).read()"

CMD ["sh", "-c", "exec uvicorn clearglass_agent_service.main:app --host 0.0.0.0 --port ${PORT}"]
