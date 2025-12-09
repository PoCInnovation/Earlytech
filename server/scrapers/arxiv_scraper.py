"""Scraper for arXiv."""

from typing import List, Dict, TYPE_CHECKING
from .base import BaseScraper

try:
    import arxiv
except ImportError:
    arxiv = None

if TYPE_CHECKING:
    from arxiv import Result


class ArxivScraper(BaseScraper):
    """Scraper for arXiv papers."""
    
    def __init__(self, category: str = "cs.LG"):
        """
        Initialize ArXiv scraper.
        
        Args:
            category: arXiv category (e.g., "cs.LG", "cs.AI")
        """
        super().__init__("arxiv")
        self.category = category
        
        if arxiv is None:
            raise ImportError("arxiv package is required. Install it with: pip install arxiv")
    
    def _normalize_result(self, paper) -> Dict:
        """Normalize arXiv result."""
        authors = ", ".join([a.name for a in paper.authors])
        link = paper.entry_id
        
        keywords_list = [paper.primary_category]
        if paper.categories:
            keywords_list.extend(paper.categories)
        
        return self.normalize_item(
            item_id=link,
            source_site=self.source_name,
            title=paper.title.replace('\n', ' '),
            description=paper.summary.replace('\n', ' '),
            author_info=authors,
            keywords=", ".join(keywords_list),
            content_url=link,
            published_date=paper.published.isoformat(),
            item_type="paper"
        )
    
    def scrape_latest(self, limit: int = 20) -> List[Dict]:
        """Scrape latest articles."""
        try:
            search = arxiv.Search(
                query=f"cat:{self.category}",
                max_results=limit,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            results = []
            for paper in search.results():
                results.append(self._normalize_result(paper))
            
            self.update_last_check()
            return results
            
        except Exception as e:
            print(f"[ERROR] ArXiv scrape_latest: {e}")
            return []
    
    def scrape_all(self, limit: int = 100) -> List[Dict]:
        """Scrape all available articles (with limit)."""
        try:
            search = arxiv.Search(
                query=f"cat:{self.category}",
                max_results=limit,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            results = []
            for paper in search.results():
                results.append(self._normalize_result(paper))
            
            self.update_last_check()
            return results
            
        except Exception as e:
            print(f"[ERROR] ArXiv scrape_all: {e}")
            return []
