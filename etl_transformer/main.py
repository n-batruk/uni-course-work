#!/usr/bin/env python3
import os
import json
import glob
from datetime import datetime

# Налаштування директорій через змінні оточення
INPUT_DIR = os.getenv("INPUT_DIR", "/data")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/transformed")

def transform():
    # Збираємо всі файли з шаблоном orders_*.json
    pattern = os.path.join(INPUT_DIR, "orders_*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"[Transform] Файли не знайдено за шляхом {pattern}")
        return

    # Зчитуємо та фільтруємо записи
    records = []
    for path in files:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for rec in data:
            # Перевіряємо наявність обов’язкових полів
            if rec.get("id") and rec.get("region") and rec.get("amount") is not None:
                records.append(rec)

    # Видаляємо дублікати за полем "id"
    unique = list({rec["id"]: rec for rec in records}.values())

    # Агрегуємо: підсумовуємо кількість та суму замовлень по регіонах
    agg = {}
    for rec in unique:
        reg = rec["region"]
        agg.setdefault(reg, {"count": 0, "total_amount": 0.0})
        agg[reg]["count"] += 1
        agg[reg]["total_amount"] += float(rec["amount"])

    # Готуємо директорію та імена файлів з часовою міткою
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    cleaned_path = os.path.join(OUTPUT_DIR, f"cleaned_{ts}.json")
    agg_path     = os.path.join(OUTPUT_DIR, f"aggregated_{ts}.json")

    # Зберігаємо очищені записи
    with open(cleaned_path, 'w', encoding='utf-8') as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
    print(f"[Transform] Очищені записи збережено: {cleaned_path}")

    # Зберігаємо агреговану статистику
    with open(agg_path, 'w', encoding='utf-8') as f:
        json.dump(agg, f, ensure_ascii=False, indent=2)
    print(f"[Transform] Агрегована статистика збережена: {agg_path}")

if __name__ == "__main__":
    transform()
