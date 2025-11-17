"""Batch job: compute embeddings for articles missing them.

Usage:
    python -m server_scrappe.pipeline.embed_missing --batch 50 --dry-run

Behaviour:
- Finds articles where embedding (pgvector) is NULL or embedding_json is NULL.
- For each article, computes embedding via `server_scrappe.pipeline.embeddings.get_embedding`.
- Stores result in `embedding` column if available (casts string to vector), otherwise in `embedding_json`.
"""
import argparse
import time
import json
from typing import Optional

from server_scrappe.db.connection import get_connection
from server_scrappe.pipeline.embeddings import get_embedding
from server_scrappe.config import DEFAULT_TIMEOUT


def has_column(conn, table: str, column: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM information_schema.columns WHERE table_name=%s AND column_name=%s",
        (table, column),
    )
    exists = cur.fetchone() is not None
    cur.close()
    return exists


def vector_extension_available(conn) -> bool:
    cur = conn.cursor()
    try:
        cur.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')")
        r = cur.fetchone()
        return bool(r[0])
    finally:
        cur.close()


def fetch_missing(conn, limit: int):
    cur = conn.cursor()
    # Fetch rows where either embedding is null or embedding_json is null
    # Build query dynamically depending on available columns
    has_embedding = has_column(conn, 'articles', 'embedding')
    has_embedding_json = has_column(conn, 'articles', 'embedding_json')

    conds = []
    if has_embedding:
        conds.append('embedding IS NULL')
    if has_embedding_json:
        conds.append('embedding_json IS NULL')
    if not conds:
        # nothing to do
        return []

    where = ' OR '.join(conds)
    sql = f"SELECT id, full_text FROM articles WHERE ({where}) ORDER BY id LIMIT %s"
    cur.execute(sql, (limit,))
    rows = cur.fetchall()
    cur.close()
    return rows, has_embedding, has_embedding_json


def store_embedding(conn, article_id: int, embedding: list, use_vector: bool):
    cur = conn.cursor()
    try:
        if use_vector:
            # store as vector; cast string literal to vector
            vec_literal = '[' + ','.join(map(str, embedding)) + ']'
            cur.execute("UPDATE articles SET embedding = %s::vector WHERE id = %s", (vec_literal, article_id))
        else:
            cur.execute("UPDATE articles SET embedding_json = %s WHERE id = %s", (json.dumps(embedding), article_id))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--batch', type=int, default=50)
    p.add_argument('--sleep', type=float, default=0.5)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    conn = get_connection()
    try:
        rows, has_embedding, has_embedding_json = fetch_missing(conn, args.batch)
        if not rows:
            print('No articles missing embeddings (or no embedding columns present).')
            return

        use_vector = False
        if has_embedding:
            # check if vector extension present
            try:
                use_vector = vector_extension_available(conn)
            except Exception:
                use_vector = False

        print(f'Found {len(rows)} articles to embed; storing to vector={use_vector} (dry_run={args.dry_run})')

        for aid, full_text in rows:
            text = full_text or ''
            if not text.strip():
                print(f'skipping id={aid} (empty full_text)')
                continue

            # Retry logic for provider calls
            emb = None
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    emb = get_embedding(text)
                except Exception as e:
                    emb = None
                    print(f'id={aid} attempt {attempt} provider error: {e}')

                if emb is not None:
                    break

                if attempt < max_attempts:
                    backoff = 2 ** (attempt - 1)
                    print(f'id={aid} retrying after {backoff}s...')
                    time.sleep(backoff)

            if emb is None:
                print(f'id={aid} embedding failed after {max_attempts} attempts — skipping')
                # continue with next article instead of aborting
                time.sleep(args.sleep)
                continue

            if args.dry_run:
                print(f'id={aid} embedding_len={len(emb)} (dry-run)')
            else:
                try:
                    store_embedding(conn, aid, emb, use_vector)
                    print(f'id={aid} stored embedding (len={len(emb)})')
                except Exception as e:
                    print(f'id={aid} store failed: {e}')

            time.sleep(args.sleep)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
