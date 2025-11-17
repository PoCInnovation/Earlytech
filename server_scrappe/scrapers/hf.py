from typing import List, Dict
from server_scrappe.scrapers.base import BaseScraper
import scrape_hf
from datetime import datetime

class HFWrapper(BaseScraper):
    def fetch(self, limit: int = 20) -> List[Dict]:
        results = []
        # We'll fetch models and spaces and map to unified structure
        try:
            models = scrape_hf.fetch_models()[:limit]
        except Exception:
            models = []
        try:
            spaces = scrape_hf.fetch_spaces()[:limit]
        except Exception:
            spaces = []

        for m in models:
            description = m.get("description") or m.get("summary") or ""
            # build a reasonable full_text from available metadata
            full_text = description
            if not full_text:
                # try fields that might contain useful text
                full_text = m.get("cardData", {}).get("description") if isinstance(m.get("cardData"), dict) else ""

            results.append({
                "title": m.get("modelId") or m.get("id"),
                "description": description,
                "summary": None,
                "tags": m.get("pipeline_tag") if isinstance(m.get("pipeline_tag"), list) else [m.get("pipeline_tag")] if m.get("pipeline_tag") else [],
                "keywords": [],
                "full_text": full_text or "",
                "source": "huggingface",
                "source_url": f"https://huggingface.co/{m.get('id')}",
                "author": m.get("author") or m.get("owner"),
                "published_at": m.get("lastModified") or datetime.utcnow(),
                "scraped_at": datetime.utcnow(),
            })

        for s in spaces:
            description = s.get("description") or ""
            full_text = description or ""
            results.append({
                "title": s.get("id"),
                "description": description,
                "summary": None,
                "tags": [s.get("task")] if s.get("task") else [],
                "keywords": [],
                "full_text": full_text,
                "source": "huggingface_space",
                "source_url": f"https://huggingface.co/{s.get('id')}",
                "author": s.get("author") or s.get("organization"),
                "published_at": s.get("lastModified") or datetime.utcnow(),
                "scraped_at": datetime.utcnow(),
            })

        return results
