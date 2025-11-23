import os
import requests
from datetime import datetime, UTC
from typing import List, Dict

# Constantes de l'outil de veille
SOURCE_SITE = "github"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") 

# ... (THEMES, HEADERS, RateLimitError, sanitize_text, normalize_github_repo, build_query_for_theme restent inchangés) ...

THEMES = [
    "large-language-model", "llm", "transformer", "text-generation", "retrieval-augmented-generation",
    "rag", "agents", "chatbot", "fine-tuning", "quantization", "lora", "peft",
    "diffusion", "stable-diffusion", "image-generation", "multimodal",
    "speech-to-text", "speech-synthesis", "audio", "reinforcement-learning",
    "computer-vision",
]

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "github-ai-theme-watcher/1.0"
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

class RateLimitError(Exception):
    def __init__(self, retry_after=None):
        self.retry_after = retry_after
        super().__init__("Rate limit hit on GitHub API. Retry after: {}".format(retry_after))

def sanitize_text(s):
    return str(s) if s is not None else ""

def normalize_github_repo(repo: Dict, theme: str) -> Dict:
    full_name = repo.get("full_name")
    keywords_list = [theme, repo.get("language") or ""]
    if repo.get("topics"):
        keywords_list.extend(repo.get("topics"))
    updated_at = repo.get("updated_at") or repo.get("pushed_at") or datetime.now(UTC).isoformat()
    return {
        "id": full_name, "source_site": SOURCE_SITE, "title": repo.get("name"),
        "description": sanitize_text(repo.get("description")), "author_info": repo.get("owner", {}).get("login", ""),
        "keywords": ", ".join(filter(None, keywords_list)), "content_url": repo.get("html_url") or f"https://github.com/{full_name}",
        "published_date": updated_at, "item_type": "repository",
    }

def build_query_for_theme(theme: str) -> str:
    theme_token = theme.replace(" ", "+")
    q = f"{theme_token} in:name,description,readme stars:>50"
    return q


def search_github_repos(query: str, per_page: int = 20) -> List[Dict]:
    """
    Recherche des repositories GitHub.
    Lève RateLimitError ou retourne List[Dict] (vide ou pleine).
    """
    url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": per_page
    }
    
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=20)
        
        if resp.status_code == 403:
            retry_after = resp.headers.get("Retry-After")
            # Lève l'erreur pour la gestion du break dans scrape_github
            raise RateLimitError(retry_after=int(retry_after) if retry_after and retry_after.isdigit() else None)
        
        # 🎯 CORRECTION CLÉ DANS CE BLOC :
        # Utiliser 'resp.raise_for_status()' si vous souhaitez détecter les 4xx/5xx généraux, 
        # mais pour la robustesse, nous allons d'abord vérifier le statut et analyser le JSON.
        
        if resp.status_code != 200:
             # Pour toutes les autres erreurs non 403, nous loguons et retournons vide.
             print(f"[WARN] HTTP Status {resp.status_code} for query: {query}")
             return []
        
        # Si le statut est 200, nous essayons d'analyser le JSON
        data = resp.json()
        return data.get("items", [])
        
    except RateLimitError:
        raise # Relance RateLimitError
    except requests.exceptions.RequestException as e:
        print(f"[ERREUR CONNEXION/HTTP] GitHub Search: {e}")
        return []
    except Exception as e:
        print(f"[ERREUR INCONNUE/JSON] GitHub Search: {e}")
        return []


def scrape_github(themes: List[str] = THEMES, limit_per_theme: int = 20) -> List[Dict]:
    """Scrape GitHub pour les thèmes donnés et retourne les éléments unifiés."""
    
    all_items = []
    stop_scraping = False # Drapeau de contrôle
    
    try:
        for theme in themes:
            if stop_scraping:
                break
                
            q = build_query_for_theme(theme)
            print(f"-> Recherche thème '{theme}' (q={q})")
            
            try:
                items = search_github_repos(q, limit_per_theme)
                
                # SÉCURITÉ SUPPLÉMENTAIRE :
                if not isinstance(items, list):
                    print(f"[FATAL WARN] search_github_repos a retourné {type(items)} au lieu de list. Arrêt.")
                    stop_scraping = True
                    continue
                
                normalized_items = [normalize_github_repo(repo, theme) for repo in items]
                all_items.extend(normalized_items)
                
            except RateLimitError:
                # Gère spécifiquement l'erreur de Rate Limit
                print(f"[RATE LIMIT] Limite atteinte. Arrêt de la veille GitHub pour cette itération.")
                stop_scraping = True
            except Exception as e:
                # Gère toutes les autres exceptions de niveau thème (très peu probables maintenant)
                print(f"[ERREUR THÈME] '{theme}': {e}")
                continue 
                
    finally:
        return all_items 

if __name__ == "__main__":
    results = scrape_github(themes=["llm"], limit_per_theme=5)
    print(f"Total GitHub items scraped: {len(results)}")
    if results:
        import json
        print("\nExemple d'élément unifié:")
        print(json.dumps(results[0], indent=2))