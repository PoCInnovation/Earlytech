"""Scraper for Hugging Face."""

import requests
from typing import List, Dict, Optional
from datetime import datetime, UTC
from .base import BaseScraper


class HuggingFaceScraper(BaseScraper):
    """Scraper for Hugging Face Hub."""
    
    def __init__(self):
        """Initialize Hugging Face scraper."""
        super().__init__("huggingface")
        self.endpoints = [
            ("models", "model"),
            ("datasets", "dataset"),
            ("spaces", "space"),
            ("collections", "collection"),
            ("papers", "paper"),
        ]
    
    def _build_url(self, item: Dict, item_type: str) -> str:
        """Build public URL for item."""
        base = "https://huggingface.co"
        item_id = item.get("id")
        
        if item_type == "model":
            return f"{base}/{item.get('modelId')}"
        elif item_type in ("dataset", "space", "collection", "paper"):
            return f"{base}/{item_id}"
        
        return base
    
    def _normalize_item(self, item: Dict, item_type: str) -> Dict:
        """Normalize Hugging Face item."""
        item_name = item.get("name") or item.get("modelId") or item.get("id")
        item_id = item.get("id") or item.get("modelId") or item.get("name")
        
        author = item.get("author") or item.get("organization", "")
        description = item.get("description", item_name)
        
        keywords_list = []
        if item.get("tags"):
            keywords_list.extend(item.get("tags"))
        if item.get("pipeline_tag"):
            tag = item.get("pipeline_tag")
            keywords_list.append(tag if isinstance(tag, str) else ", ".join(tag))
        
        last_modified = item.get("lastModified") or item.get("last_modified") or datetime.now(UTC).isoformat()
        
        return self.normalize_item(
            item_id=item_id,
            source_site=self.source_name,
            title=item_name,
            description=description,
            author_info=author,
            keywords=", ".join(keywords_list),
            content_url=self._build_url(item, item_type),
            published_date=last_modified,
            item_type=item_type
        )
    
    def _fetch_endpoint(self, endpoint: str, item_type: str, limit: int = 20) -> List[Dict]:
        """Fetch data from specific endpoint."""
        url = f"https://huggingface.co/api/{endpoint}?sort=lastModified&direction=-1&limit={limit}"
        
        try:
            r = requests.get(url, timeout=20)
            
            if r.status_code == 404:
                return []
            
            r.raise_for_status()
            
            items = r.json()
            return [self._normalize_item(item, item_type) for item in items]
            
        except Exception as e:
            print(f"[ERROR] HF {item_type}: {e}")
            return []
    
    def scrape_latest(self, limit: int = 20) -> List[Dict]:
        """Scrape latest items."""
        all_items = []
        items_per_endpoint = max(1, limit // len(self.endpoints))
        
        for endpoint, item_type in self.endpoints:
            items = self._fetch_endpoint(endpoint, item_type, items_per_endpoint)
            all_items.extend(items)
        
        self.update_last_check()
        return all_items[:limit]
    
    def scrape_all(self, limit: int = 100) -> List[Dict]:
        """Scrape all available items."""
        all_items = []
        items_per_endpoint = max(1, limit // len(self.endpoints))
        
        for endpoint, item_type in self.endpoints:
            items = self._fetch_endpoint(endpoint, item_type, items_per_endpoint)
            all_items.extend(items)
        
        self.update_last_check()
        return all_items[:limit]
