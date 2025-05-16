FROM python:3.9-slim

WORKDIR /app

COPY etl_loader/main.py .
COPY etl_loader/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV DB_HOST="localhost" \
    DB_PORT="5432" \
    DB_NAME="etl_db" \
    DB_USER="etl_user" \
    DB_PASSWORD="password" \
    INPUT_DIR="/transformed"

ENTRYPOINT ["python", "main.py"]
