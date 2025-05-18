#!/usr/bin/env python3
import os, requests, json, time
from datetime import datetime
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

API_URL   = os.getenv("SOURCE_API_URL")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
PUSHGATEWAY = os.getenv("PUSHGATEWAY", "pushgateway:9091")
JOB_NAME    = "etl_extractor"

def fetch_and_save():
    start = time.time()
    resp = requests.get(API_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"orders_{ts}.json"
    path = os.path.join(OUTPUT_DIR, filename)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    duration = time.time() - start

    registry = CollectorRegistry()
    Gauge('etl_records_extracted', 'Number of records extracted', registry=registry).set(len(data))
    Gauge('etl_extract_duration_seconds', 'Duration of extract job', registry=registry).set(duration)
    push_to_gateway(PUSHGATEWAY, job=JOB_NAME, registry=registry)

    print(f"[Extract] Збережено {len(data)} записів у {path} за {duration:.2f}s")

if __name__ == "__main__":
    fetch_and_save()
