"""Runner simple pour lancer tous les scrapers et stocker les résultats dans Postgres.
Usage:
    python -m server_scrappe.main --limit 10
    python path/to/server_scrappe/main.py --limit 10  # also supported
"""
import argparse
import sys
import os

# Ensure project root is on sys.path so imports work whether we run
# `python -m server_scrappe.main` (package mode) or `python main.py`
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Support running either as a package (python -m server_scrappe.main) or
# directly from the `server_scrappe/` directory (python main.py).
try:
    from server_scrappe.config import ensure_dirs
    from server_scrappe.scrapers.medium import MediumWrapper
    from server_scrappe.scrapers.github import GithubWrapper
    from server_scrappe.scrapers.le_monde import LeMondeWrapper
    from server_scrappe.scrapers.hf import HFWrapper
    from server_scrappe.scrapers.arxiv import ArxivWrapper
    from server_scrappe.db.models import upsert_article
except ModuleNotFoundError:
    # Fallback to local imports when running `python main.py` inside the package dir
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    from config import ensure_dirs
    from scrapers.medium import MediumWrapper
    from scrapers.github import GithubWrapper
    from scrapers.le_monde import LeMondeWrapper
    from scrapers.hf import HFWrapper
    from scrapers.arxiv import ArxivWrapper
    from db.models import upsert_article


def run_all(limit: int = 20):
    ensure_dirs()
    scrapers = [
        MediumWrapper(),
        GithubWrapper(),
        LeMondeWrapper(),
        HFWrapper(),
        ArxivWrapper(),
    ]

    total = 0
    for s in scrapers:
        print(f"Running {s.__class__.__name__}...")
        try:
            items = s.fetch(limit=limit)
            for it in items:
                try:
                    upsert_article(it)
                    total += 1
                except Exception as e:
                    print(f"[ERROR] upsert failed: {e}")
        except Exception as e:
            print(f"[ERROR] scraper {s.__class__.__name__} failed: {e}")

    print(f"Done. {total} items processed and pushed to DB.")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=10)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_all(limit=args.limit)
