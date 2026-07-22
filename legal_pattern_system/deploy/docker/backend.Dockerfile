FROM python:3.12-slim

WORKDIR /app
COPY web/backend/requirements-web.txt /app/web/backend/requirements-web.txt
RUN pip install --no-cache-dir -r /app/web/backend/requirements-web.txt

COPY . /app
WORKDIR /app/web/backend

EXPOSE 8000
CMD ["sh", "-c", "python ../../scripts/init_database.py && uvicorn app:app --host 0.0.0.0 --port 8000"]
