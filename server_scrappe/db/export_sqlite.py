"""Export PostgreSQL table(s) to a SQLite .db file.

Usage:
    python -m server_scrappe.db.export_sqlite --out ../data/earlytech.db --tables articles

This script connects to Postgres using `DATABASE_URL` from `server_scrappe.config`.
It exports selected tables (default: `articles`) to the target SQLite file.

Notes:
- Types are converted conservatively: arrays and jsonb are serialized to JSON strings.
- Vector/pgvector columns are serialized to text (if present).
"""
import argparse
import json
import sqlite3
from pathlib import Path
from typing import List

import psycopg2
import psycopg2.extras

from server_scrappe.config import DATABASE_URL


PG_TO_SQLITE = {
    'integer': 'INTEGER',
    'bigint': 'INTEGER',
    'smallint': 'INTEGER',
    'serial': 'INTEGER',
    'bigserial': 'INTEGER',
    'text': 'TEXT',
    'varchar': 'TEXT',
    'character varying': 'TEXT',
    'timestamp without time zone': 'TEXT',
    'timestamp with time zone': 'TEXT',
    'date': 'TEXT',
    'boolean': 'INTEGER',
    'json': 'TEXT',
    'jsonb': 'TEXT',
    'text[]': 'TEXT',
}


def map_type(pg_type: str) -> str:
    t = pg_type.lower()
    # simple mapping, fallback to TEXT
    return PG_TO_SQLITE.get(t, 'TEXT')


def get_columns(conn, table: str):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = %s
    ORDER BY ordinal_position
    """, (table,))
    cols = cur.fetchall()
    cur.close()
    return cols


def export_table(pg_conn, sqlite_conn, table: str):
    cols = get_columns(pg_conn, table)
    if not cols:
        print(f"Table {table} not found in Postgres.")
        return

    col_defs = []
    col_names = []
    for c in cols:
        name = c['column_name']
        dtype = c['data_type']
        col_names.append(name)
        col_defs.append(f'"{name}" {map_type(dtype)}')

    create_sql = f'CREATE TABLE IF NOT EXISTS "{table}" ({", ".join(col_defs)});'
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute(create_sql)
    sqlite_conn.commit()

    pg_cur = pg_conn.cursor()
    pg_cur.execute(f'SELECT {", ".join(col_names)} FROM "{table}"')

    insert_sql = f'INSERT INTO "{table}" ({", ".join(["\""+n+"\"" for n in col_names])}) VALUES ({", ".join(["?" for _ in col_names])})'

    batch = []
    for row in pg_cur:
        out = []
        for v, c in zip(row, cols):
            dtype = c['data_type']
            # Normalize common complex types to JSON/text for SQLite
            if v is None:
                out.append(None)
            elif isinstance(v, (list, tuple)):
                try:
                    out.append(json.dumps(list(v)))
                except Exception:
                    out.append(str(v))
            elif isinstance(v, dict):
                try:
                    out.append(json.dumps(v))
                except Exception:
                    out.append(str(v))
            elif dtype in ('json', 'jsonb'):
                out.append(json.dumps(v))
            else:
                # timestamps -> iso
                try:
                    if hasattr(v, 'isoformat'):
                        out.append(v.isoformat())
                    else:
                        out.append(v)
                except Exception:
                    out.append(str(v))
        batch.append(tuple(out))

    if batch:
        sqlite_cur.executemany(insert_sql, batch)
        sqlite_conn.commit()

    pg_cur.close()
    sqlite_cur.close()
    print(f"Exported {len(batch)} rows from {table} to SQLite.")


def main(argv: List[str] = None):
    p = argparse.ArgumentParser()
    p.add_argument('--out', '-o', default='../data/earlytech.db', help='Output SQLite file path')
    p.add_argument('--tables', '-t', default='articles', help='Comma-separated list of tables to export')
    args = p.parse_args(argv)

    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL not set in environment or .env')

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    tables = [t.strip() for t in args.tables.split(',') if t.strip()]

    print(f"Connecting to Postgres ({DATABASE_URL.split('@')[0]}@...) and exporting tables: {tables}")
    pg_conn = psycopg2.connect(DATABASE_URL)
    sqlite_conn = sqlite3.connect(str(out_path))

    try:
        for t in tables:
            export_table(pg_conn, sqlite_conn, t)
    finally:
        pg_conn.close()
        sqlite_conn.close()

    print(f"Done. SQLite DB written to: {out_path}")


if __name__ == '__main__':
    main()
