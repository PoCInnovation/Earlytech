import os
import time
import sqlite3
import requests
from datetime import datetime

REPOS = [
    "huggingface/transformers",
    "openai/openai-python",
    "pytorch/pytorch",
    "tensorflow/tensorflow",
    "langchain/langchain",
    "microsoft/ML-For-Beginners",
    "microsoft/AI-For-Beginners",
    "karpathy/nn-zero-to-hero",
    "Significant-Gravitas/AutoGPT",
    "stabilityai/stablediffusion",
]
INTERVAL = 300
DB_FILE = os.path.join(os.path.dirname(__file__), "github_releases.db")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS releases (
    id TEXT PRIMARY KEY,
    repo TEXT,
    tag TEXT,
    name TEXT,
    published TIMESTAMP,
    body TEXT,
    html_url TEXT
)
""")
conn.commit()

headers = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

def fetch_releases(repo):
    url = f"https://api.github.com/repos/{repo}/releases"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()

def save_release(repo, release):
    cur.execute("""
    INSERT OR IGNORE INTO releases (id, repo, tag, name, published, body, html_url)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        release["id"],
        repo,
        release.get("tag_name", ""),
        release.get("name", ""),
        release.get("published_at", datetime.utcnow().isoformat()),
        release.get("body", ""),
        release.get("html_url", "")
    ))
    conn.commit()

def load_seen_ids():
    cur.execute("SELECT id FROM releases")
    return set(row[0] for row in cur.fetchall())

def main():
    print("Initialisation GitHub Releases...")
    seen_ids = load_seen_ids()
    print(f"{len(seen_ids)} releases déjà enregistrées.")
    try:
        while True:
            for repo in REPOS:
                try:
                    releases = fetch_releases(repo)
                    for rel in releases:
                        rel_id = str(rel["id"])
                        if rel_id not in seen_ids:
                            print(f"[NOUVELLE RELEASE] {repo} → {rel.get('name','(no name)')}")
                            print(" ->", rel.get("html_url", ""))
                            save_release(repo, rel)
                            seen_ids.add(rel_id)
                except Exception as e:
                    print(f"[ERREUR] {repo}: {e}")

            print(f"Attente {INTERVAL}s avant prochaine vérification...")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("Arrêt manuel.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
