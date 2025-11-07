import time
import os
import sqlite3
import feedparser
from datetime import datetime

FEEDS = [
    # Flux par catégorie
    "https://www.lemonde.fr/bresil/rss_full.xml",
    "https://www.lemonde.fr/international/rss_full.xml",
    "https://www.lemonde.fr/actualite-medias/rss_full.xml",
    # Flux "en continu"
    "https://www.lemonde.fr/en_continu/rss_full.xml"
]

DB_FILE = os.path.join(os.path.dirname(__file__), "lemonde_articles.db")
INTERVAL = 300

conn = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS articles (
    id TEXT PRIMARY KEY,
    title TEXT,
    published TIMESTAMP,
    summary TEXT,
    link TEXT,
    feed TEXT
)
""")
conn.commit()

def save_article(entry, feed_url):
    """
    entry: objet feedparser entry
    """
    entry_id = getattr(entry, "id", None) or getattr(entry, "link", None)
    title = getattr(entry, "title", "")
    link = getattr(entry, "link", "")
    summary = getattr(entry, "summary", "")
    published = None
    if getattr(entry, "published_parsed", None):
        published = datetime.fromtimestamp(time.mktime(entry.published_parsed))
    elif getattr(entry, "updated_parsed", None):
        published = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
    else:
        published = datetime.utcnow()

    cur.execute("""
    INSERT OR IGNORE INTO articles (id, title, published, summary, link, feed)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (entry_id, title, published, summary, link, feed_url))
    conn.commit()

def load_seen_ids():
    cur.execute("SELECT id FROM articles")
    return set(row[0] for row in cur.fetchall())

def fetch_feed(feed_url):
    return feedparser.parse(feed_url)

def main():
    print("Initialisation...")
    seen_ids = load_seen_ids()
    print(f"{len(seen_ids)} articles déjà en base.")
    try:
        while True:
            for feed in FEEDS:
                try:
                    d = fetch_feed(feed)
                    if d.bozo:
                        print(f"[WARN] Problème lecture flux {feed}: {getattr(d, 'bozo_exception', '')}")
                        continue

                    for entry in d.entries:
                        entry_id = getattr(entry, "id", None) or getattr(entry, "link", None)
                        if entry_id is None:
                            continue
                        if entry_id not in seen_ids:
                            print(f"[NOUVEAU] {entry.get('title','(no title)')}")
                            print(" ->", entry.get("link",""))
                            save_article(entry, feed)
                            seen_ids.add(entry_id)
                except Exception as e:
                    print(f"[ERREUR] du fetch du feed {feed}: {e}")

            print(f"Attente {INTERVAL}s avant prochaine vérification...")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("Arrêt par l'utilisateur.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
