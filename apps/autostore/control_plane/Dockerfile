FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY autostore ./autostore
EXPOSE 8000
CMD ["uvicorn", "autostore.app:app", "--host", "0.0.0.0", "--port", "8000"]
