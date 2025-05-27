#!/usr/bin/env python3
import os, json, glob, psycopg2 # type: ignore
from psycopg2.extras import execute_values # type: ignore

# Env vars
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "etl_db")
DB_USER     = os.getenv("DB_USER", "etl_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
INPUT_DIR   = os.getenv("INPUT_DIR", "/transformed")

def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )

def load_cleaned(conn):
    files = sorted(glob.glob(os.path.join(INPUT_DIR, "cleaned_*.json")))
    for path in files:
        with open(path, 'r', encoding='utf-8') as f:
            records = json.load(f)
        rows = [
            (rec["id"], rec["postId"], rec.get("name"), rec.get("email"), rec.get("body"))
            for rec in records
        ]
        sql = """
        CREATE TABLE IF NOT EXISTS raw_comments (
          id INTEGER PRIMARY KEY,
          post_id INTEGER NOT NULL,
          name TEXT,
          email TEXT,
          body TEXT,
          loaded_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
        );
        INSERT INTO raw_comments (id, post_id, name, email, body)
        VALUES %s
        ON CONFLICT (id) DO UPDATE
          SET post_id = EXCLUDED.post_id,
              name    = EXCLUDED.name,
              email   = EXCLUDED.email,
              body    = EXCLUDED.body,
              loaded_at = now();
        """
        with conn.cursor() as cur:
            execute_values(cur, sql, rows)
        conn.commit()
        print(f"[Load] Loaded {len(rows)} comments into raw_comments from {path}")

def load_aggregated(conn):
    files = sorted(glob.glob(os.path.join(INPUT_DIR, "aggregated_*.json")))
    for path in files:
        with open(path, 'r', encoding='utf-8') as f:
            agg = json.load(f)
        rows = [
            (int(post_id), stats["count"], stats["total_words"])
            for post_id, stats in agg.items()
        ]
        sql = """
        CREATE TABLE IF NOT EXISTS agg_comments_by_post (
          post_id INTEGER PRIMARY KEY,
          comment_count INTEGER NOT NULL,
          total_words INTEGER NOT NULL,
          updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
        );
        INSERT INTO agg_comments_by_post (post_id, comment_count, total_words)
        VALUES %s
        ON CONFLICT (post_id) DO UPDATE
          SET comment_count = EXCLUDED.comment_count,
              total_words   = EXCLUDED.total_words,
              updated_at    = now();
        """
        with conn.cursor() as cur:
            execute_values(cur, sql, rows)
        conn.commit()
        print(f"[Load] Loaded {len(rows)} posts into agg_comments_by_post from {path}")

if __name__ == "__main__":
    conn = get_conn()
    try:
        load_cleaned(conn)
        load_aggregated(conn)
    finally:
        conn.close()
