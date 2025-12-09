"""Abstract base class for all scrapers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime, UTC


class BaseScraper(ABC):
    """Abstract base class defining interface for all scrapers."""
    
    def __init__(self, source_name: str):
        """
        Initialize scraper.
        
        Args:
            source_name: Unique source name (e.g., "arxiv", "github", "medium")
        """
        self.source_name = source_name
        self.last_check = None
    
    @abstractmethod
    def scrape_latest(self, limit: int = 20) -> List[Dict]:
        """
        Scrape latest articles/items from source.
        Used in watch mode (polling).
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List of normalized items
        """
        pass
    
    @abstractmethod
    def scrape_all(self, limit: int = 100) -> List[Dict]:
        """
        Scrape all available articles/items.
        Used in backfill mode (history).
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List of normalized items
        """
        pass
    
    def update_last_check(self):
        """Update last check timestamp."""
        self.last_check = datetime.now(UTC)
    
    @staticmethod
    def normalize_item(
        item_id: str,
        source_site: str,
        title: str,
        description: str,
        author_info: str,
        keywords: str,
        content_url: str,
        published_date: str,
        item_type: str = "article"
    ) -> Dict:
        """
        Normalize item to unified format.
        
        Returns:
            Dict with unified structure
        """
        return {
            "id": item_id,
            "source_site": source_site,
            "title": title,
            "description": description,
            "author_info": author_info,
            "keywords": keywords,
            "content_url": content_url,
            "published_date": published_date,
            "item_type": item_type,
        }
