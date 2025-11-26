import feedparser
import time
from datetime import datetime
from typing import List, Dict

SOURCE_SITE = "le_monde"

FEEDS = [
    "https://www.lemonde.fr/international/rss_full.xml",
    "https://www.lemonde.fr/actualite-medias/rss_full.xml",
    "https://www.lemonde.fr/en_continu/rss_full.xml"
]

def normalize_lemonde_entry(entry: feedparser.FeedParserDict, feed_url: str) -> Dict:
    """Normalise une entrée RSS Le Monde dans le format unifié."""
    entry_id = getattr(entry, "id", None) or getattr(entry, "link", None)
    
    published_date = datetime.utcnow().isoformat()
    if getattr(entry, "published_parsed", None):
        published_date = datetime.fromtimestamp(time.mktime(entry.published_parsed)).isoformat()
    elif getattr(entry, "updated_parsed", None):
        published_date = datetime.fromtimestamp(time.mktime(entry.updated_parsed)).isoformat()
        
    category = "actualité générale"
    if "international" in feed_url:
        category = "international"
    elif "medias" in feed_url:
        category = "actualité médias"
    elif "continu" in feed_url:
        category = "en continu"

    return {
        "id": entry_id,
        "source_site": SOURCE_SITE,
        "title": getattr(entry, "title", ""),
        "description": getattr(entry, "summary", ""),
        "author_info": getattr(entry, "author", "Le Monde"),
        "keywords": category,
        "content_url": getattr(entry, "link", ""),
        "published_date": published_date,
        "item_type": "article",
    }

def scrape_lemonde(feeds: List[str] = FEEDS) -> List[Dict]:
    """Scrape les flux RSS Le Monde et retourne les éléments unifiés."""
    all_items = []
    unique_ids = set()

    for feed_url in feeds:
        try:
            d = feedparser.parse(feed_url)
            
            for entry in d.entries:
                entry_id = getattr(entry, "id", None) or getattr(entry, "link", None)
                if entry_id and entry_id not in unique_ids:
                    all_items.append(normalize_lemonde_entry(entry, feed_url))
                    unique_ids.add(entry_id)
                    
        except Exception as e:
            print(f"[ERREUR] du fetch du feed {feed_url}: {e}")
        time.sleep(1)

    return all_items

if __name__ == "__main__":
    results = scrape_lemonde(feeds=FEEDS[:1])
    print(f"Total Le Monde items scraped: {len(results)}")
    if results:
        print("\nExemple d'élément unifié:")
        import json
        print(json.dumps(results[0], indent=2))