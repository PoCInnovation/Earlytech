"""Scraper for Medium."""

from typing import List, Dict
from .base import BaseScraper

try:
    import feedparser
except ImportError:
    feedparser = None


class MediumScraper(BaseScraper):
    """Scraper for Medium articles."""
    
    def __init__(self):
        """Initialize Medium scraper."""
        super().__init__("medium")
        self.feeds = [
            "https://medium.com/feed/tag/artificial-intelligence",
            "https://medium.com/feed/tag/machine-learning",
            "https://medium.com/feed/tag/deep-learning",
            "https://medium.com/feed/tag/ai",
        ]
        
        if feedparser is None:
            raise ImportError("feedparser package is required. Install it with: pip install feedparser")
    
    def _normalize_entry(self, entry: Dict) -> Dict:
        """Normalize RSS entry from Medium."""
        import time
        from datetime import datetime
        
        entry_id = entry.get('link', '')
        
        published_date = datetime.utcnow().isoformat()
        if getattr(entry, "published_parsed", None):
            published_date = datetime.fromtimestamp(time.mktime(entry.published_parsed)).isoformat()
        
        keywords = [tag.term for tag in entry.get('tags', [])] if 'tags' in entry else []
        
        return self.normalize_item(
            item_id=entry_id,
            source_site=self.source_name,
            title=entry.get('title', 'N/A'),
            description=entry.get('summary', 'N/A'),
            author_info=entry.get('author', 'N/A'),
            keywords=", ".join(keywords),
            content_url=entry_id,
            published_date=published_date,
            item_type="article"
        )
    
    def scrape_latest(self, limit: int = 20) -> List[Dict]:
        """Scrape latest articles."""
        import time
        
        all_items = []
        unique_links = set()
        items_per_feed = limit // len(self.feeds) + 1
        
        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:items_per_feed]:
                    link = entry.get('link')
                    if link and link not in unique_links:
                        all_items.append(self._normalize_entry(entry))
                        unique_links.add(link)
                
                time.sleep(1)
            except Exception as e:
                print(f"[ERROR] Medium feed {feed_url}: {e}")
        
        self.update_last_check()
        return all_items[:limit]
    
    def scrape_all(self, limit: int = 100) -> List[Dict]:
        """Scrape all available articles."""
        import time
        
        all_items = []
        unique_links = set()
        items_per_feed = limit // len(self.feeds) + 1
        
        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:items_per_feed]:
                    link = entry.get('link')
                    if link and link not in unique_links:
                        all_items.append(self._normalize_entry(entry))
                        unique_links.add(link)
                
                time.sleep(1)
            except Exception as e:
                print(f"[ERROR] Medium feed {feed_url}: {e}")
        
        self.update_last_check()
        return all_items[:limit]
