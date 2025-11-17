from typing import List, Dict
from server_scrappe.scrapers.base import BaseScraper
import arxiv
from datetime import datetime
import requests
from server_scrappe.config import PDF_DIR
from pathlib import Path

# Optional PDF text extraction
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except Exception:
    PDFPLUMBER_AVAILABLE = False


def download_pdf(entry_id: str, target_dir: str = PDF_DIR) -> str:
    """Download arXiv PDF and return path, or empty string on failure.
    entry_id example: 'http://arxiv.org/abs/...'"""
    try:
        if entry_id.endswith('.pdf'):
            pdf_url = entry_id
        else:
            pdf_url = entry_id.replace('/abs/', '/pdf/') + '.pdf'
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        filename = pdf_url.split('/')[-1]
        target_path = Path(target_dir) / filename
        r = requests.get(pdf_url, timeout=30)
        r.raise_for_status()
        with open(target_path, 'wb') as f:
            f.write(r.content)
        # try to extract text if pdfplumber available
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(target_path) as pdf:
                    text = "\n\n".join(p.extract_text() or "" for p in pdf.pages)
                # write extracted text next to pdf
                txt_path = target_path.with_suffix('.txt')
                with open(txt_path, 'w', encoding='utf-8') as tf:
                    tf.write(text)
                return str(target_path)
            except Exception:
                return str(target_path)
        return str(target_path)
    except Exception:
        return ""

class ArxivWrapper(BaseScraper):
    def fetch(self, limit: int = 10) -> List[Dict]:
        results = []
        search = arxiv.Search(
            query=f"cat:cs.LG",
            max_results=limit,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        for result in search.results():
            pdf_path = download_pdf(result.entry_id)
            results.append({
                "title": result.title,
                "description": result.summary,
                "summary": result.summary,
                "tags": [],
                "keywords": [],
                "full_text": result.summary,
                "source": "arxiv",
                "source_url": result.entry_id,
                "author": ", ".join([a.name for a in result.authors]),
                "published_at": result.published,
                "scraped_at": datetime.utcnow(),
                "pdf_path": pdf_path,
            })
        return results
