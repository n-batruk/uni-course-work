#!/usr/bin/env python3
import os, requests, json, time
from datetime import datetime
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import psycopg2
from psycopg2.extras import execute_values

# ─── Configuration ─────────────────────────────────────────────────────────────
API_URL     = os.getenv("SOURCE_API_URL")
OUTPUT_DIR  = os.getenv("OUTPUT_DIR", "/data")
PUSHGATEWAY = os.getenv("PUSHGATEWAY", "pushgateway:9091")

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "etl_db")
DB_USER     = os.getenv("DB_USER", "etl_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

JOB_NAME    = "etl_extractor"

# ─── Helpers ───────────────────────────────────────────────────────────────────
def get_db_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def save_raw_to_postgres(records):
    """
    Create table raw_extracted (if needed) and insert each record as JSONB.
    """
    create_sql = """
    CREATE TABLE IF NOT EXISTS raw_extracted (
      id            SERIAL PRIMARY KEY,
      payload       JSONB NOT NULL,
      extracted_at  TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
    );
    """
    insert_sql = """
    INSERT INTO raw_extracted (payload)
    VALUES %s
    """
    # Prepare a list of one‐column tuples for execute_values
    values = [(json.dumps(rec),) for rec in records]

    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(create_sql)
            execute_values(cur, insert_sql, values)
        conn.commit()
        print(f"[Extract→DB] Inserted {len(values)} rows into raw_extracted")
    finally:
        conn.close()

# ─── Main logic ────────────────────────────────────────────────────────────────
def fetch_and_save():
    start = time.time()
    resp = requests.get(API_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # 1) Save to disk
    ts       = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"orders_{ts}.json"
    path     = os.path.join(OUTPUT_DIR, filename)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    duration = time.time() - start

    # 2) Push Prometheus metrics
    registry = CollectorRegistry()
    Gauge('etl_records_extracted',    'Number of records extracted', registry=registry).set(len(data))
    Gauge('etl_extract_duration_seconds','Duration of extract job', registry=registry).set(duration)
    push_to_gateway(PUSHGATEWAY, job=JOB_NAME, registry=registry)

    print(f"[Extract] Saved {len(data)} records to {path} in {duration:.2f}s")

    # 3) Also push raw payloads into Postgres
    save_raw_to_postgres(data)

if __name__ == "__main__":
    fetch_and_save()
