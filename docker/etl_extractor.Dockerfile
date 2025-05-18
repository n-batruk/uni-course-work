FROM python:3.9-slim

WORKDIR /app

COPY etl_extractor/main.py .
COPY etl_extractor/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV SOURCE_API_URL="https://jsonplaceholder.typicode.com/comments" \
    OUTPUT_DIR="/data"

ENTRYPOINT ["python", "main.py"]
