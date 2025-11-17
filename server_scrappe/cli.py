"""Simple CLI front for common tasks: db, scrapp, embedd, save, clean, status, all

Usage examples:
    python -m server_scrappe.cli db
    python -m server_scrappe.cli scrapp --limit 50
    python -m server_scrappe.cli embedd --batch 200 --dry-run
    python -m server_scrappe.cli save --out ../data/earlytech.db
    python -m server_scrappe.cli clean
    python -m server_scrappe.cli status
"""
from __future__ import annotations
import argparse
import shutil
from pathlib import Path
import sys

from server_scrappe.db import init_db as db_init_module
from server_scrappe.scripts import fetch_and_embed
from server_scrappe.pipeline import embed_missing
from server_scrappe.db import export_sqlite
from server_scrappe.db.connection import get_connection


def cmd_db(args):
    print("[cli] Initialising DB (creating extensions/tables)...")
    db_init_module.init_db()


def cmd_scrapp(args):
    limit = args.limit or 20
    print(f"[cli] Fetching and upserting items (limit per source={limit})...")
    items = fetch_and_embed.fetch_all(limit_per_source=limit)
    print(f"[cli] Fetched {len(items)} items — upserting...")
    fetch_and_embed.upsert_bulk(items)
    print("[cli] Upsert done.")


def cmd_embedd(args):
    argv_backup = sys.argv
    try:
        sys.argv = [argv_backup[0]]
        if args.dry_run:
            sys.argv += ['--dry-run']
        if args.batch:
            sys.argv += ['--batch', str(args.batch)]
        embed_missing.main()
    finally:
        sys.argv = argv_backup


def cmd_save(args):
    out = args.out or '../data/earlytech.db'
    argv = ['--out', out]
    if args.tables:
        argv += ['--tables', args.tables]
    print(f"[cli] Exporting tables to SQLite: {out}")
    export_sqlite.main(argv)


def cmd_clean(args):
    # remove downloaded pdfs and extracted txts
    pdf_dir = Path('data/pdfs')
    removed = 0
    if pdf_dir.exists():
        for p in pdf_dir.rglob('*'):
            try:
                p.unlink()
                removed += 1
            except Exception:
                pass
        try:
            shutil.rmtree(pdf_dir)
        except Exception:
            pass
    # remove exported sqlite default
    sqlite_path = Path('data/earlytech.db')
    if sqlite_path.exists():
        try:
            sqlite_path.unlink()
            removed += 1
        except Exception:
            pass
    print(f"[cli] Cleaned files (approx removed entries): {removed}")


def cmd_status(args):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT COUNT(*) FROM articles')
        total = cur.fetchone()[0]
    except Exception:
        total = None
    # check embedding column
    has_vector = False
    try:
        cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='articles' AND column_name='embedding')")
        has_vector = cur.fetchone()[0]
    except Exception:
        has_vector = False

    emb_count = None
    try:
        if has_vector:
            cur.execute('SELECT COUNT(*) FROM articles WHERE embedding IS NOT NULL')
        else:
            cur.execute("SELECT COUNT(*) FROM articles WHERE embedding_json IS NOT NULL")
        emb_count = cur.fetchone()[0]
    except Exception:
        emb_count = None

    print(f"[cli] total_articles={total} embeddings_present={emb_count} vector_column={has_vector}")
    cur.close()
    conn.close()


def main(argv: list[str] | None = None):
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd')

    sub.add_parser('db')

    s_scrapp = sub.add_parser('scrapp')
    s_scrapp.add_argument('--limit', type=int, default=20)

    s_emb = sub.add_parser('embedd')
    s_emb.add_argument('--batch', type=int, default=100)
    s_emb.add_argument('--dry-run', action='store_true')

    s_save = sub.add_parser('save')
    s_save.add_argument('--out', default='../data/earlytech.db')
    s_save.add_argument('--tables', default='articles')

    sub.add_parser('clean')
    sub.add_parser('status')

    sub.add_parser('all')

    args = p.parse_args(argv)

    if args.cmd == 'db':
        cmd_db(args)
    elif args.cmd == 'scrapp':
        cmd_scrapp(args)
    elif args.cmd == 'embedd':
        cmd_embedd(args)
    elif args.cmd == 'save':
        cmd_save(args)
    elif args.cmd == 'clean':
        cmd_clean(args)
    elif args.cmd == 'status':
        cmd_status(args)
    elif args.cmd == 'all':
        cmd_db(args)
        cmd_scrapp(args)
        cmd_embedd(args)
        cmd_save(args)
    else:
        p.print_help()


if __name__ == '__main__':
    main()
