#!/usr/bin/env python3
import os, psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT")
DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )

def transform():
    conn = get_conn()
    with conn.cursor() as cur:
        # 1) filter & dedupe raw_extracted → clean_comments
        cur.execute("""
        CREATE TABLE IF NOT EXISTS clean_comments AS
        SELECT DISTINCT
          (payload->>'id')::int    AS id,
          (payload->>'postId')::int AS post_id,
          payload->>'name'         AS name,
          payload->>'email'        AS email,
          payload->>'body'         AS body,
          now()                    AS transformed_at
        FROM raw_extracted;
        """)
        # 2) aggregate → agg_comments_by_post
        cur.execute("""
        CREATE TABLE IF NOT EXISTS agg_comments_by_post AS
        SELECT
          post_id,
          COUNT(*)         AS comment_count,
          SUM(LENGTH(body) - LENGTH(REPLACE(body, ' ', '')) + 1) AS total_words,
          now()            AS transformed_at
        FROM clean_comments
        GROUP BY post_id;
        """)
    conn.commit()
    conn.close()
    print("[Transform] Data written to clean_comments and agg_comments_by_post")

if __name__ == "__main__":
    transform()
