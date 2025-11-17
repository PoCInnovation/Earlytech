"""
Small runner to fetch from all wrappers, upsert into DB and optionally run embeddings.
Usage:
    python -m server_scrappe.scripts.fetch_and_embed --limit 50 --embed --dry-run
"""
import argparse
import time
from server_scrappe.scrapers.arxiv import ArxivWrapper
from server_scrappe.scrapers.github import GithubWrapper
from server_scrappe.scrapers.hf import HFWrapper
from server_scrappe.scrapers.le_monde import LeMondeWrapper
from server_scrappe.scrapers.medium import MediumWrapper
from server_scrappe.db.models import upsert_article
from server_scrappe.db.connection import get_connection
from server_scrappe.pipeline import embed_missing

WRAPPERS = [
    ArxivWrapper,
    GithubWrapper,
    HFWrapper,
    LeMondeWrapper,
    MediumWrapper,
]


def fetch_all(limit_per_source: int = 50):
    all_items = []
    for W in WRAPPERS:
        try:
            w = W()
        except Exception:
            # Some wrappers (like MediumWrapper) expect no args or instantiate inner classes
            w = W()
        try:
            items = w.fetch(limit=limit_per_source)
            print(f"Fetched {len(items)} items from {W.__name__}")
            all_items.extend(items)
        except Exception as e:
            print(f"Error fetching from {W.__name__}: {e}")
    return all_items


def upsert_bulk(items, delay: float = 0.0):
    conn = None
    try:
        for i, it in enumerate(items, 1):
            try:
                upsert_article(it)
            except Exception as e:
                print(f"Upsert failed for item {i}: {e}")
            if delay and i < len(items):
                time.sleep(delay)
    finally:
        if conn:
            conn.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--limit', type=int, default=20, help='limit per source')
    p.add_argument('--embed', action='store_true', help='run embedding after upsert')
    p.add_argument('--dry-run', action='store_true', help='pass to embedding script to avoid writes')
    p.add_argument('--batch', type=int, default=100, help='batch size for embedding fetch_missing')
    args = p.parse_args()

    items = fetch_all(limit_per_source=args.limit)
    print(f"Total fetched items: {len(items)}")
    if not items:
        print("No items fetched — aborting upsert.")
        return

    upsert_bulk(items)

    if args.embed:
        # call embed_missing.main programmatically
        import sys
        argv_backup = sys.argv
        try:
            sys.argv = [argv_backup[0]]
            if args.dry_run:
                sys.argv += ['--dry-run']
            sys.argv += ['--batch', str(args.batch)]
            embed_missing.main()
        finally:
            sys.argv = argv_backup


if __name__ == '__main__':
    main()
