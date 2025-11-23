import requests
from datetime import datetime, UTC # Importation de UTC
from typing import List, Dict

# Constantes de l'outil de veille
SOURCE_SITE = "huggingface"

def build_url(item: Dict, item_type: str) -> str:
    """Construit l’URL publique de l’élément"""
    base = "https://huggingface.co"
    item_id = item.get("id")
    if item_type == "model":
        return f"{base}/{item.get('modelId')}"
    # Correction de la liste pour inclure tous les types pertinents
    elif item_type in ("dataset", "space", "collection", "paper"): 
        return f"{base}/{item_id}"
    return base

def normalize_huggingface_item(item: Dict, item_type: str) -> Dict:
    """Normalise un élément Hugging Face dans le format unifié."""
    # Déterminer le nom et l'ID
    item_name = item.get("name") or item.get("modelId") or item.get("id")
    item_id = item.get("id") or item.get("modelId") or item.get("name")
    
    # Déterminer l'auteur
    author = item.get("author") or item.get("organization", "")
    
    # Déterminer la description/le résumé (souvent pas disponible dans la liste, on utilise le 'name' ou 'id' par défaut)
    description = item.get("description", item_name)
    
    # Déterminer les mots-clés
    keywords_list = []
    if item.get("tags"):
        keywords_list.extend(item.get("tags"))
    if item.get("pipeline_tag"):
        tag = item.get("pipeline_tag")
        keywords_list.append(tag if isinstance(tag, str) else ", ".join(tag))
    
    # Déterminer la date - Utilisation de datetime.now(UTC)
    last_modified = item.get("lastModified") or item.get("last_modified") or datetime.now(UTC).isoformat()

    return {
        "id": item_id,
        "source_site": SOURCE_SITE,
        "title": item_name,
        "description": description,
        "author_info": author,
        "keywords": ", ".join(keywords_list),
        "content_url": build_url(item, item_type),
        "published_date": last_modified,
        "item_type": item_type,
    }

def fetch_huggingface_api(endpoint: str, item_type: str, limit: int = 20) -> List[Dict]:
    """Récupère les données d'un endpoint spécifique et les normalise."""
    url = f"https://huggingface.co/api/{endpoint}?sort=lastModified&direction=-1&limit={limit}"
    
    try:
        # Aucune en-tête d'authentification envoyée
        r = requests.get(url, timeout=20)
        
        if r.status_code == 404:
            return []
        
        # Gère les autres erreurs (4xx/5xx) si elles surviennent
        r.raise_for_status()
        
        items = r.json()
        
        # Normalisation des données
        normalized_items = [normalize_huggingface_item(item, item_type) for item in items]
        return normalized_items
        
    except Exception as e:
        print(f"[ERREUR] HF {item_type}: {e}")
        return []

def scrape_huggingface(limit_per_type: int = 20) -> List[Dict]:
    """Scrape le Hugging Face Hub, ignorant l'endpoint 'organizations'."""
    
    # 🛑 L'entrée "organizations" a été retirée pour éviter l'erreur 401
    fetchers = [
        ("models", "model"),
        ("datasets", "dataset"),
        ("spaces", "space"),
        ("collections", "collection"),
        ("papers", "paper"),
    ]
    
    all_items = []
    
    for endpoint, item_type in fetchers:
        items = fetch_huggingface_api(endpoint, item_type, limit_per_type)
        all_items.extend(items)
        
    return all_items

if __name__ == "__main__":
    results = scrape_huggingface(limit_per_type=5)
    print(f"Total Hugging Face items scraped: {len(results)}")
    if results:
        print("\nExemple d'élément unifié:")
        import json
        print(json.dumps(results[0], indent=2))