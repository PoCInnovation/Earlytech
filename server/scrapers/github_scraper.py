"""Scraper for GitHub."""

import os
import requests
from typing import List, Dict, Optional
from .base import BaseScraper


class GithubScraper(BaseScraper):
    """Scraper for GitHub repositories."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub scraper.
        
        Args:
            token: GitHub token (optional, loads from GITHUB_TOKEN env var)
        """
        super().__init__("github")
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.themes = [
            "large-language-model", "llm", "transformer", "text-generation",
            "retrieval-augmented-generation", "rag", "agents", "chatbot",
            "fine-tuning", "quantization", "lora", "peft", "diffusion",
            "stable-diffusion", "image-generation", "multimodal",
            "speech-to-text", "speech-synthesis", "audio",
            "reinforcement-learning", "computer-vision",
        ]
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "server-ai-watcher/1.0"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
    
    def _normalize_repo(self, repo: Dict, theme: str) -> Dict:
        """Normalize GitHub repository."""
        full_name = repo.get("full_name")
        keywords_list = [theme, repo.get("language") or ""]
        if repo.get("topics"):
            keywords_list.extend(repo.get("topics"))
        
        updated_at = repo.get("updated_at") or repo.get("pushed_at")
        
        return self.normalize_item(
            item_id=full_name,
            source_site=self.source_name,
            title=repo.get("name"),
            description=repo.get("description") or "",
            author_info=repo.get("owner", {}).get("login", ""),
            keywords=", ".join(filter(None, keywords_list)),
            content_url=repo.get("html_url") or f"https://github.com/{full_name}",
            published_date=updated_at,
            item_type="repository"
        )
    
    def _search_repos(self, query: str, per_page: int = 20) -> List[Dict]:
        """Search repositories with given query."""
        url = "https://api.github.com/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": per_page
        }
        
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=20)
            
            if resp.status_code == 403:
                retry_after = resp.headers.get("Retry-After")
                raise Exception(f"GitHub rate limit hit. Retry after: {retry_after}")
            
            if resp.status_code != 200:
                print(f"[WARN] GitHub API returned {resp.status_code}")
                return []
            
            data = resp.json()
            return data.get("items", [])
            
        except Exception as e:
            print(f"[ERROR] GitHub search: {e}")
            return []
    
    def scrape_latest(self, limit: int = 20) -> List[Dict]:
        """Scrape latest repositories for themes."""
        results = []
        items_per_theme = max(1, limit // len(self.themes))
        
        for theme in self.themes:
            query = f"{theme} in:name,description,readme stars:>50"
            repos = self._search_repos(query, per_page=items_per_theme)
            
            for repo in repos:
                results.append(self._normalize_repo(repo, theme))
        
        self.update_last_check()
        return results[:limit]
    
    def scrape_all(self, limit: int = 100) -> List[Dict]:
        """Scrape all available repositories (with limit)."""
        results = []
        items_per_theme = max(1, limit // len(self.themes))
        
        for theme in self.themes:
            query = f"{theme} in:name,description,readme stars:>10"
            repos = self._search_repos(query, per_page=items_per_theme)
            
            for repo in repos:
                results.append(self._normalize_repo(repo, theme))
        
        self.update_last_check()
        return results[:limit]
