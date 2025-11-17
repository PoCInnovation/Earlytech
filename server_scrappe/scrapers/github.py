from typing import List, Dict
from server_scrappe.scrapers.base import BaseScraper
import scrape_github
from datetime import datetime
import requests
from server_scrappe.config import GITHUB_TOKEN

class GithubWrapper(BaseScraper):
    def fetch(self, limit: int = 20) -> List[Dict]:
        results = []
        # Re-use search logic from scrape_github; build a small set of themes
        THEMES = [
            "large-language-model",
            "llm",
            "transformer",
            "text-generation",
        ]
        seen = set()
        for theme in THEMES:
            try:
                q = scrape_github.build_query_for_theme(theme)
                items = scrape_github.search_github_repos(q, per_page=limit)
                for repo in items:
                    full_name = repo.get("full_name")
                    if not full_name or full_name in seen:
                        continue
                    seen.add(full_name)
                    results.append({
                        "title": repo.get("name"),
                        "description": repo.get("description"),
                        "summary": None,
                        "tags": [repo.get("language")] if repo.get("language") else [],
                        "keywords": [],
                        # Try to fetch README raw from common branches; fallback to description
                        "full_text": _fetch_github_readme_fulltext(repo) or (repo.get("description") or ""),
                        "source": "github",
                        "source_url": repo.get("html_url"),
                        "author": repo.get("owner", {}).get("login") if repo.get("owner") else None,
                        "published_at": repo.get("updated_at"),
                        "scraped_at": datetime.utcnow(),
                    })
            except Exception as e:
                print(f"[WARN] github wrapper error for theme {theme}: {e}")
        return results


def _fetch_github_readme_fulltext(repo: Dict) -> str:
    """Try to fetch README from raw.githubusercontent.com using common branches.
    Returns text or empty string on failure.
    """
    full_name = repo.get("full_name")
    if not full_name:
        return ""

    branches = ["main", "master", "HEAD"]
    headers = {}
    token = GITHUB_TOKEN or getattr(scrape_github, 'GITHUB_TOKEN', None)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for br in branches:
        raw_url = f"https://raw.githubusercontent.com/{full_name}/{br}/README.md"
        try:
            r = requests.get(raw_url, headers=headers, timeout=10)
            if r.status_code == 200 and r.text:
                return r.text
        except Exception:
            continue

    return ""
