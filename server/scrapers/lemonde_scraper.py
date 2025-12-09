"""Scraper for Le Monde."""

from typing import List, Dict
from .base import BaseScraper

try:
    import feedparser
except ImportError:
    feedparser = None


class LeMondeScraper(BaseScraper):
    """Scraper for Le Monde articles."""
    
    def __init__(self):
        """Initialize Le Monde scraper."""
        super().__init__("le_monde")
        self.feeds = [
            "https://www.lemonde.fr/international/rss_full.xml",
            "https://www.lemonde.fr/actualite-medias/rss_full.xml",
            "https://www.lemonde.fr/en_continu/rss_full.xml"
        ]
        
        if feedparser is None:
            raise ImportError("feedparser package is required. Install it with: pip install feedparser")
    
    def _normalize_entry(self, entry: Dict, feed_url: str) -> Dict:
        """Normalize RSS entry from Le Monde."""
        import time
        from datetime import datetime
        
        entry_id = getattr(entry, "id", None) or getattr(entry, "link", None)
        
        published_date = datetime.utcnow().isoformat()
        if getattr(entry, "published_parsed", None):
            published_date = datetime.fromtimestamp(time.mktime(entry.published_parsed)).isoformat()
        elif getattr(entry, "updated_parsed", None):
            published_date = datetime.fromtimestamp(time.mktime(entry.updated_parsed)).isoformat()
        
        category = "general news"
        if "international" in feed_url:
            category = "international"
        elif "medias" in feed_url:
            category = "media news"
        elif "continu" in feed_url:
            category = "continuous"
        
        return self.normalize_item(
            item_id=entry_id,
            source_site=self.source_name,
            title=getattr(entry, "title", ""),
            description=getattr(entry, "summary", ""),
            author_info=getattr(entry, "author", "Le Monde"),
            keywords=category,
            content_url=getattr(entry, "link", ""),
            published_date=published_date,
            item_type="article"
        )
    
    def scrape_latest(self, limit: int = 20) -> List[Dict]:
        """Scrape latest articles."""
        import time
        
        all_items = []
        unique_ids = set()
        items_per_feed = limit // len(self.feeds) + 1
        
        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:items_per_feed]:
                    entry_id = getattr(entry, "id", None) or getattr(entry, "link", None)
                    if entry_id and entry_id not in unique_ids:
                        all_items.append(self._normalize_entry(entry, feed_url))
                        unique_ids.add(entry_id)
                
                time.sleep(1)
            except Exception as e:
                print(f"[ERROR] Le Monde feed {feed_url}: {e}")
        
        self.update_last_check()
        return all_items[:limit]
    
    def scrape_all(self, limit: int = 100) -> List[Dict]:
        """Scrape all available articles."""
        import time
        
        all_items = []
        unique_ids = set()
        items_per_feed = limit // len(self.feeds) + 1
        
        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:items_per_feed]:
                    entry_id = getattr(entry, "id", None) or getattr(entry, "link", None)
                    if entry_id and entry_id not in unique_ids:
                        all_items.append(self._normalize_entry(entry, feed_url))
                        unique_ids.add(entry_id)
                
                time.sleep(1)
            except Exception as e:
                print(f"[ERROR] Le Monde feed {feed_url}: {e}")
        
        self.update_last_check()
        return all_items[:limit]
