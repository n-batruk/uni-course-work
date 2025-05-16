#!/usr/bin/env python3
import os
import json
import glob
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# Налаштування через змінні оточення
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "etl_db")
DB_USER     = os.getenv("DB_USER", "etl_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
INPUT_DIR   = os.getenv("INPUT_DIR", "/transformed")

# Функція підключення до БД
def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def load_cleaned(conn):
    """Завантаження очищених записів у таблицю raw_orders."""
    files = sorted(glob.glob(os.path.join(INPUT_DIR, "cleaned_*.json")))
    for path in files:
        with open(path, 'r', encoding='utf-8') as f:
            records = json.load(f)
        # Підготуємо кортежі для upsert
        rows = [(rec["id"], rec["region"], float(rec["amount"])) for rec in records]
        sql = """
        CREATE TABLE IF NOT EXISTS raw_orders (
            id TEXT PRIMARY KEY,
            region TEXT NOT NULL,
            amount NUMERIC NOT NULL,
            loaded_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
        );
        INSERT INTO raw_orders (id, region, amount)
        VALUES %s
        ON CONFLICT (id) DO UPDATE
          SET region = EXCLUDED.region,
              amount = EXCLUDED.amount,
              loaded_at = now();
        """
        with conn.cursor() as cur:
            execute_values(cur, sql, rows)
        conn.commit()
        print(f"[Load] Завантажено {len(rows)} строк в raw_orders з файлу {os.path.basename(path)}")

def load_aggregated(conn):
    """Завантаження агрегованої статистики у таблицю agg_orders_by_region."""
    files = sorted(glob.glob(os.path.join(INPUT_DIR, "aggregated_*.json")))
    for path in files:
        with open(path, 'r', encoding='utf-8') as f:
            agg = json.load(f)
        rows = [
            (region, stats["count"], stats["total_amount"])
            for region, stats in agg.items()
        ]
        sql = """
        CREATE TABLE IF NOT EXISTS agg_orders_by_region (
            region TEXT PRIMARY KEY,
            order_count INTEGER NOT NULL,
            total_amount NUMERIC NOT NULL,
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
        );
        INSERT INTO agg_orders_by_region (region, order_count, total_amount)
        VALUES %s
        ON CONFLICT (region) DO UPDATE
          SET order_count = EXCLUDED.order_count,
              total_amount = EXCLUDED.total_amount,
              updated_at = now();
        """
        with conn.cursor() as cur:
            execute_values(cur, sql, rows)
        conn.commit()
        print(f"[Load] Завантажено {len(rows)} регіонів в agg_orders_by_region з файлу {os.path.basename(path)}")

if __name__ == "__main__":
    conn = get_conn()
    try:
        load_cleaned(conn)
        load_aggregated(conn)
    finally:
        conn.close()
