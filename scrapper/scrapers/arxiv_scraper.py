"""Scraper for arXiv."""

from typing import List, Dict, TYPE_CHECKING
from .base import BaseScraper
import requests
from datetime import datetime
import io

try:
    import arxiv
except ImportError:
    arxiv = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

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
    
    def _extract_pdf_text(self, pdf_url: str) -> str:
        """Download and extract text from arXiv PDF."""
        if PyPDF2 is None:
            return ""
        
        try:
            response = requests.get(pdf_url, timeout=30)
            if response.status_code != 200:
                return ""
            
            pdf_file = io.BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            full_text = '\n'.join(text_parts)
            return full_text
            
        except Exception as e:
            print(f"[WARN] PDF extraction failed for {pdf_url}: {e}")
            return ""
    
    def _fetch_full_content(self, paper) -> str:
        """Fetch full paper content from arXiv PDF."""
        try:
            pdf_url = paper.pdf_url
            pdf_text = self._extract_pdf_text(pdf_url)
            
            if pdf_text:
                full_content = f"""{paper.title}

Authors: {', '.join([a.name for a in paper.authors])}

Category: {paper.primary_category}

Published: {paper.published.strftime('%Y-%m-%d')}

Abstract:
{paper.summary}

Full Paper Content:
{pdf_text}"""
                return full_content
            else:
                full_content = f"""{paper.title}

Authors: {', '.join([a.name for a in paper.authors])}

Category: {paper.primary_category}

{paper.summary}"""
                return full_content
        except Exception as e:
            print(f"[WARN] Content fetch failed: {e}")
            return paper.summary
        return ""
    
    def _normalize_result(self, paper) -> Dict:
        """Normalize arXiv result."""
        authors = ", ".join([a.name for a in paper.authors])
        link = paper.entry_id
        
        keywords_list = [paper.primary_category]
        if paper.categories:
            keywords_list.extend(paper.categories)
        
        full_content = self._fetch_full_content(paper)
        if not full_content:
            full_content = paper.summary.replace('\n', ' ')
        
        return self.normalize_item(
            item_id=link,
            source_site=self.source_name,
            title=paper.title.replace('\n', ' '),
            description=paper.summary.replace('\n', ' '),
            full_content=full_content,
            author_info=authors,
            keywords=", ".join(keywords_list),
            content_url=link,
            published_date=paper.published.isoformat(),
            item_type="paper"
        )
    
    def _perform_search(self, limit: int) -> List[Dict]:
        """Perform search with given limit."""
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
            print(f"[ERROR] ArXiv search: {e}")
            return []

    def scrape_latest(self, limit: int = 20) -> List[Dict]:
        """Scrape latest articles."""
        return self._perform_search(limit)
    
    def scrape_all(self, limit: int = 100) -> List[Dict]:
        """Scrape all available articles (with limit)."""
        return self._perform_search(limit)
