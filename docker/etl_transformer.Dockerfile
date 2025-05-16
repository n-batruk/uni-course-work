# Базовий образ з Python
FROM python:3.9-slim

# Робоча директорія
WORKDIR /app

# Копіюємо код та dependencies-файл
COPY etl_transformer/main.py .
COPY etl_transformer/requirements.txt .

# Встановлюємо (якщо в requirements щось є)
RUN pip install --no-cache-dir -r requirements.txt

# Змінні оточення для вхідної та вихідної тек
ENV INPUT_DIR="/data" \
    OUTPUT_DIR="/transformed"

# Точка входу
ENTRYPOINT ["python", "main.py"]
