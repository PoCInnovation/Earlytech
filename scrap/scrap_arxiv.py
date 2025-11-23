import arxiv
from datetime import datetime
from typing import List, Dict

# Constantes de l'outil de veille
SOURCE_SITE = "arxiv"
CATEGORY = "cs.LG" 

def normalize_arxiv_result(paper: arxiv.Result) -> Dict:
    """Normalise un résultat arXiv dans le format unifié."""
    
    authors = ", ".join([a.name for a in paper.authors])
    
    link = paper.entry_id
    
    keywords_list = [paper.primary_category]
    if paper.categories:
        keywords_list.extend(paper.categories)
    
    return {
        "id": link,
        "source_site": SOURCE_SITE,
        "title": paper.title.replace('\n', ' '),
        "description": paper.summary.replace('\n', ' '),
        "author_info": authors,
        "keywords": ", ".join(keywords_list),
        "content_url": link,
        "published_date": paper.published.isoformat(),
        "item_type": "paper",
    }

def scrape_arxiv(category: str = CATEGORY, max_results: int = 10) -> List[Dict]:
    """Scrape arXiv pour une catégorie et retourne les éléments unifiés."""
    
    try:
        search = arxiv.Search(
            query=f"cat:{category}",
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        normalized_results = []
        for result in search.results():
            normalized_results.append(normalize_arxiv_result(result))
            
        return normalized_results
        
    except Exception as e:
        print(f"[ERREUR] arXiv Search: {e}")
        return []

if __name__ == "__main__":
    results = scrape_arxiv(max_results=5)
    print(f"Total arXiv items scraped: {len(results)}")
    if results:
        print("\nExemple d'élément unifié:")
        import json
        print(json.dumps(results[0], indent=2))