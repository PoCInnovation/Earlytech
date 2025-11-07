#!/usr/bin/env python3
"""
github_ai_theme_watcher.py

Veille thématique GitHub orientée IA — recherche de projets par thème (ex: "LLM", "diffusion", "RAG", ...)
Stocke des résultats synthétiques dans une base SQLite pour consommation par un dashboard / newsletter / alertes.

Usage:
    python github_ai_theme_watcher.py        # tourne en continu (sleep INTERVAL)
    python github_ai_theme_watcher.py --once # exécute une seule itération (utile pour cron/tests)

Configure via variables en tête du fichier ou via variables d'environnement:
    - GITHUB_TOKEN: token (optionnel mais recommandé)
"""

import os
import sys
import time
import sqlite3
import requests
import argparse
from datetime import datetime
from typing import List


THEMES = [
    "large-language-model",
    "llm",
    "transformer",
    "text-generation",
    "retrieval-augmented-generation",
    "rag",
    "agents",
    "chatbot",
    "fine-tuning",
    "quantization",
    "lora",
    "peft",
    "diffusion",
    "stable-diffusion",
    "image-generation",
    "multimodal",
    "speech-to-text",
    "speech-synthesis",
    "audio",
    "reinforcement-learning",
    "computer-vision",
]

RESULTS_PER_THEME = 20

INTERVAL = int(os.getenv("GITHUB_WATCHER_INTERVAL", 21600))

DB_FILE = os.path.join(os.path.dirname(__file__), "github_ai_trending.db")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "github-ai-theme-watcher/1.0"
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS trending_ai_projects (
    full_name TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    stars INTEGER,
    language TEXT,
    theme TEXT,
    updated_at TEXT,
    html_url TEXT,
    last_seen TIMESTAMP
)
""")
conn.commit()

cur.execute("""
CREATE TABLE IF NOT EXISTS project_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    stars INTEGER,
    updated_at TEXT,
    captured_at TIMESTAMP
)
""")
conn.commit()


def search_github_repos(query: str, per_page: int = RESULTS_PER_THEME) -> List[dict]:
    """
    Recherche des repositories GitHub via l'API Search.
    `query` doit être la Q de recherche (ex: "transformer language:python").
    """
    url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": per_page
    }
    resp = requests.get(url, headers=HEADERS, params=params, timeout=20)
    if resp.status_code == 403:
        retry_after = resp.headers.get("Retry-After")
        raise RateLimitError(retry_after=int(retry_after) if retry_after and retry_after.isdigit() else None)
    resp.raise_for_status()
    data = resp.json()
    return data.get("items", [])

def sanitize_text(s):
    if s is None:
        return ""
    return str(s)

def save_project(repo: dict, theme: str):
    """INSERT OR REPLACE de l'enregistrement principal + ajout historique."""
    full_name = repo.get("full_name")
    name = repo.get("name")
    desc = sanitize_text(repo.get("description"))
    stars = repo.get("stargazers_count", 0)
    language = repo.get("language") or ""
    updated_at = repo.get("updated_at") or repo.get("pushed_at") or datetime.utcnow().isoformat()
    html_url = repo.get("html_url") or f"https://github.com/{full_name}"
    now = datetime.utcnow().isoformat()

    cur.execute("""
    INSERT OR REPLACE INTO trending_ai_projects
    (full_name, name, description, stars, language, theme, updated_at, html_url, last_seen)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (full_name, name, desc, stars, language, theme, updated_at, html_url, now))
    conn.commit()

    cur.execute("""
    INSERT INTO project_history (full_name, stars, updated_at, captured_at)
    VALUES (?, ?, ?, ?)
    """, (full_name, stars, updated_at, now))
    conn.commit()


class RateLimitError(Exception):
    def __init__(self, retry_after=None):
        self.retry_after = retry_after
        super().__init__("Rate limit hit on GitHub API. Retry after: {}".format(retry_after))


def build_query_for_theme(theme: str) -> str:
    theme_token = theme.replace(" ", "+")
    q = f"{theme_token} in:name,description,readme stars:>50"

    return q

def run_once(themes=THEMES):
    print(f"[{datetime.utcnow().isoformat()}] Démarrage d'une itération de veille (thèmes: {len(themes)})")
    total_saved = 0
    for theme in themes:
        try:
            q = build_query_for_theme(theme)
            print(f"-> Recherche thème '{theme}' (q={q})")
            items = search_github_repos(q)
            print(f"   ↳ {len(items)} résultats récupérés pour '{theme}'")
            for repo in items:
                save_project(repo, theme)
                total_saved += 1
        except RateLimitError as rle:
            wait = rle.retry_after or 60
            print(f"[RATE LIMIT] Limit atteint. Pause {wait} secondes.")
            time.sleep(wait)
        except Exception as e:
            print(f"[ERREUR] thème '{theme}': {e}")
    print(f"[{datetime.utcnow().isoformat()}] Itération terminée — {total_saved} enregistrements traités.")
    return total_saved

def main_loop(interval=INTERVAL, once=False):
    if once:
        run_once()
        return

    try:
        while True:
            run_once()
            print(f"Attente {interval} secondes avant la prochaine vérification...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("")
    finally:
        conn.close()

def parse_args():
    p = argparse.ArgumentParser(description="Veille thématique GitHub orientée IA")
    p.add_argument("--once", action="store_true", help="Exécuter une unique itération et quitter")
    p.add_argument("--interval", type=int, default=INTERVAL, help="Intervalle entre itérations (secondes)")
    p.add_argument("--themes", type=str, help="Liste de thèmes séparés par des virgules (remplace la config)")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    if args.themes:
        THEMES = [t.strip() for t in args.themes.split(",") if t.strip()]
        print(f"Themes remplacés: {THEMES}")

    INTERVAL = args.interval

    print("Github AI Theme Watcher démarré.")
    if GITHUB_TOKEN:
        print("")
    else:
        print("")

    main_loop(interval=INTERVAL, once=args.once)
