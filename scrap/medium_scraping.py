import feedparser
from datetime import datetime
from typing import List, Dict, Optional
import time

# Constantes de l'outil de veille
SOURCE_SITE = "medium"

RSS_FEEDS = [
    "https://medium.com/feed/tag/artificial-intelligence",
    "https://medium.com/feed/tag/machine-learning",
    "https://medium.com/feed/tag/deep-learning",
    "https://medium.com/feed/tag/ai",
]

def normalize_medium_entry(entry: feedparser.FeedParserDict) -> Dict:
    """Normalise une entrée RSS Medium dans le format unifié."""
    entry_id = entry.get('link', '')
    
    # Conversion de la date
    published_date = datetime.utcnow().isoformat()
    if getattr(entry, "published_parsed", None):
        published_date = datetime.fromtimestamp(time.mktime(entry.published_parsed)).isoformat()
    
    keywords = [tag.term for tag in entry.get('tags', [])] if 'tags' in entry else []

    return {
        "id": entry_id,
        "source_site": SOURCE_SITE,
        "title": entry.get('title', 'N/A'),
        "description": entry.get('summary', 'N/A'),
        "author_info": entry.get('author', 'N/A'),
        "keywords": ", ".join(keywords),
        "content_url": entry_id,
        "published_date": published_date,
        "item_type": "article",
    }

def scrape_medium(max_articles_per_feed: int = 10) -> List[Dict]:
    """Scrape les flux RSS Medium et retourne les éléments unifiés."""
    all_items = []
    unique_links = set()

    for feed_url in RSS_FEEDS:
        print(f"📡 Fetching RSS: {feed_url}")
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:max_articles_per_feed]:
                link = entry.get('link')
                if link and link not in unique_links:
                    all_items.append(normalize_medium_entry(entry))
                    unique_links.add(link)
            
        except Exception as e:
            print(f"❌ Error fetching {feed_url}: {e}")
        time.sleep(1) # Respecter une pause entre les appels RSS

    return all_items

if __name__ == "__main__":
    results = scrape_medium(max_articles_per_feed=2)
    print(f"Total Medium items scraped: {len(results)}")
    if results:
        print("\nExemple d'élément unifié:")
        import json
        print(json.dumps(results[0], indent=2))