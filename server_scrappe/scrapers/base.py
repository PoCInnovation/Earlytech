from typing import Dict, List

class BaseScraper:
    """Interface for scrapers: implement fetch() to return list of normalized dicts."""

    def fetch(self, limit: int = 10) -> List[Dict]:
        raise NotImplementedError()
