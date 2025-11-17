from typing import List, Dict
from server_scrappe.scrapers.base import BaseScraper
import feedparser
from datetime import datetime

FEEDS = [
    "https://www.lemonde.fr/bresil/rss_full.xml",
    "https://www.lemonde.fr/international/rss_full.xml",
    "https://www.lemonde.fr/actualite-medias/rss_full.xml",
    "https://www.lemonde.fr/en_continu/rss_full.xml",
]

class LeMondeWrapper(BaseScraper):
    def fetch(self, limit: int = 20) -> List[Dict]:
        results = []
        for feed in FEEDS:
            d = feedparser.parse(feed)
            entries = d.entries[:limit]
            for entry in entries:
                entry_id = getattr(entry, "id", None) or getattr(entry, "link", None)
                published = None
                if getattr(entry, "published_parsed", None):
                    import time
                    published = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                else:
                    published = datetime.utcnow()

                results.append({
                    "title": getattr(entry, "title", ""),
                    "description": getattr(entry, "summary", ""),
                    "summary": getattr(entry, "summary", ""),
                    "tags": [],
                    "keywords": [],
                    "full_text": getattr(entry, "summary", ""),
                    "source": "le_monde",
                    "source_url": getattr(entry, "link", ""),
                    "author": getattr(entry, "author", ""),
                    "published_at": published,
                    "scraped_at": datetime.utcnow(),
                })
        return results
