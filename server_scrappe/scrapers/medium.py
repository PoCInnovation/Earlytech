from typing import List, Dict, Optional
from server_scrappe.scrapers.base import BaseScraper
import medium_scraping
from datetime import datetime


class MediumWrapper(BaseScraper):
    """Wrapper around the existing `medium_scraping.py` to return normalized dicts."""

    def __init__(self):
        self.inner = medium_scraping.MediumScraper()

    def fetch(self, limit: int = 10) -> List[Dict]:
        entries = self.inner.scrape_articles_from_rss(max_articles=limit, delay=1)
        results = []
        for e in entries:
            results.append({
                "title": e.get("title"),
                "description": None,
                "summary": e.get("summary") if e.get("summary") else None,
                "tags": e.get("tags", []),
                "keywords": [],
                "full_text": e.get("content"),
                "source": "medium",
                "source_url": e.get("url") or e.get("link"),
                "author": e.get("author"),
                "published_at": e.get("publish_date"),
                "scraped_at": datetime.utcnow().isoformat(),
            })
        return results
