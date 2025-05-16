# Базовий образ з Python
FROM python:3.9-slim

# Робоча директорія
WORKDIR /app

# Копіюємо код і залежності
COPY etl_extractor/main.py .
COPY etl_extractor/requirements.txt .

# Встановлюємо пакети
RUN pip install --no-cache-dir -r requirements.txt

# Змінні оточення (можна перевизначити при запуску)
ENV SOURCE_API_URL="https://jsonplaceholder.typicode.com/comments" \
    OUTPUT_DIR="/data"

# Точка входу
ENTRYPOINT ["python", "main.py"]
