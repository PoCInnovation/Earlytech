import os
import time
import sqlite3
import requests
from datetime import datetime

INTERVAL = 300  

DB_FILE = os.path.join(os.path.dirname(__file__), "huggingface_hub.db")
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS hubs (
    id TEXT PRIMARY KEY,
    name TEXT,
    author TEXT,
    likes INTEGER,
    downloads INTEGER,
    task TEXT,
    last_modified TEXT,
    type TEXT,
    url TEXT
)
""")
conn.commit()


def fetch_models():
    """Récupère les modèles récents via l’API Hugging Face"""
    url = "https://huggingface.co/api/models?sort=lastModified&direction=-1&limit=20"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

def fetch_datasets():
    """Récupère les datasets récents"""
    url = "https://huggingface.co/api/datasets?sort=lastModified&direction=-1&limit=20"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

def fetch_spaces():
    """Récupère les Spaces récents"""
    url = "https://huggingface.co/api/spaces?sort=lastModified&direction=-1&limit=20"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

def fetch_collections():
    """Récupère les collections récentes"""
    url = "https://huggingface.co/api/collections?sort=lastModified&direction=-1&limit=20"
    r = requests.get(url, timeout=20)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    return r.json()

def fetch_organizations():
    """Récupère les organisations récentes"""
    url = "https://huggingface.co/api/organizations?limit=20"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

def fetch_papers():
    """Récupère les papiers de recherche récents (si API accessible)"""
    url = "https://huggingface.co/api/papers?sort=lastModified&direction=-1&limit=20"
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def save_item(item, item_type):
    cur.execute("""
    INSERT OR IGNORE INTO hubs (id, name, author, likes, downloads, task, last_modified, type, url)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item.get("id"),
        item.get("name") or item.get("modelId") or item.get("id"),
        item.get("author") or item.get("organization", ""),
        item.get("likes", 0),
        item.get("downloads", 0),
        ", ".join(item.get("pipeline_tag", "")) if isinstance(item.get("pipeline_tag"), list) else item.get("pipeline_tag", ""),
        item.get("lastModified") or item.get("last_modified") or datetime.utcnow().isoformat(),
        item_type,
        build_url(item, item_type)
    ))
    conn.commit()

def build_url(item, item_type):
    """Construit l’URL publique de l’élément"""
    base = "https://huggingface.co"
    if item_type in ("model", "dataset", "space", "collection", "organization"):
        return f"{base}/{item.get('id')}"
    elif item_type == "paper":
        return f"{base}/papers/{item.get('id')}"
    return base

def load_seen_ids():
    cur.execute("SELECT id FROM hubs")
    return set(row[0] for row in cur.fetchall())


def main():
    print("Initialisation Hugging Face Hub Watcher...")
    seen_ids = load_seen_ids()
    print(f"{len(seen_ids)} éléments déjà enregistrés.")

    fetchers = [
        ("model", fetch_models),
        ("dataset", fetch_datasets),
        ("space", fetch_spaces),
        ("collection", fetch_collections),
        ("organization", fetch_organizations),
        ("paper", fetch_papers)
    ]

    try:
        while True:
            for item_type, fetch_func in fetchers:
                try:
                    items = fetch_func()
                    for item in items:
                        item_id = item.get("id")
                        if item_id and item_id not in seen_ids:
                            print(f"[NOUVEAU {item_type.upper()}] {item_id}")
                            save_item(item, item_type)
                            seen_ids.add(item_id)
                except Exception as e:
                    print(f"[ERREUR] {item_type}: {e}")

            print(f"Attente {INTERVAL}s avant prochaine vérification...\n")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("Arrêt manuel.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
