FROM python:3.9-slim

WORKDIR /app

COPY etl_transformer/main.py .
COPY etl_transformer/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV INPUT_DIR="/data" \
    OUTPUT_DIR="/transformed"

ENTRYPOINT ["python", "main.py"]
