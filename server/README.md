# Serveur de Veille Technique

Serveur de scraping et d'indexation avec 2 modes de fonctionnement.

## Architecture

Le serveur est organisé autour de plusieurs composants :

### 1. **Scrapers** (`scrapers/`)
Chaque source a son propre scraper qui implémente l'interface `BaseScraper` :
- `ArxivScraper` : Articles arXiv (cs.LG)
- `GithubScraper` : Repositories GitHub trending
- `MediumScraper` : Articles Medium (AI/ML tags)
- `LeMondeScraper` : Articles Le Monde
- `HuggingFaceScraper` : Models, datasets, spaces sur HuggingFace

### 2. **DatabaseManager** (`database.py`)
Gère la persistance des données :
- Table `articles` : Articles normalisés
- Table `embeddings` : Vecteurs d'embedding pour chaque article
- Table `sync_history` : Historique des synchronisations

### 3. **EmbeddingManager** (`embeddings.py`)
Crée les embeddings pour les articles :
- Supports multiple providers (Dummy, SentenceTransformers)
- Sérialise les embeddings en format bytes pour la base de données

### 4. **WatchServer** (`main.py`)
Orchestrateur principal avec 2 modes.

## Modes de fonctionnement

### Mode "Backfill" (Historique)
```bash
python main.py backfill --limit 100
```
- Scrape tout l'historique disponible depuis chaque source
- Sauvegarde et crée les embeddings
- S'exécute une seule fois au démarrage
- Idéal pour remplir la base de données initialement

### Mode "Watch" (Veille)
```bash
python main.py watch --interval 300
```
- Lance une boucle infinie
- Scrape les nouvelles articles régulièrement (par défaut toutes les 5 min)
- Ajoute à la base et crée les embeddings automatiquement
- Peut tourner indéfiniment

### Mode "Stats"
```bash
python main.py stats
```
- Affiche les statistiques actuelles de la base de données

## Installation

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## Utilisation

### Démarrage simple
```bash
# Mode backfill pour remplir la BD
python main.py backfill

# Puis mode watch en continu
python main.py watch
```

### Avec options
```bash
# Backfill avec limite 50 par source, base de données custom
python main.py backfill --limit 50 --db custom.db

# Watch avec intervalle 10 min (600 sec)
python main.py watch --interval 600

# Vérifier les stats
python main.py stats --db custom.db
```

## Format unifié des articles

Chaque article scrappé est normalisé dans ce format :

```python
{
    "id": "unique-identifier",
    "source_site": "arxiv|github|medium|le_monde|huggingface",
    "title": "Titre de l'article",
    "description": "Résumé ou description",
    "author_info": "Auteur(s)",
    "keywords": "keyword1, keyword2, ...",
    "content_url": "https://link-to-original",
    "published_date": "2024-01-15T10:30:00Z",
    "item_type": "article|paper|repository|..."
}
```

## Structure de la base de données

### Table `articles`
```sql
id (TEXT PRIMARY KEY)
source_site (TEXT)
title (TEXT)
description (TEXT)
author_info (TEXT)
keywords (TEXT)
content_url (TEXT)
published_date (TEXT)
item_type (TEXT)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

### Table `embeddings`
```sql
id (INTEGER PRIMARY KEY)
article_id (TEXT UNIQUE)
embedding (BLOB) -- Vecteur sérialisé
embedding_model (TEXT)
created_at (TIMESTAMP)
```

### Table `sync_history`
```sql
id (INTEGER PRIMARY KEY)
source_site (TEXT)
sync_mode (TEXT) -- "watch" ou "backfill"
last_sync_time (TIMESTAMP)
items_processed (INTEGER)
created_at (TIMESTAMP)
```

## Ajouter une nouvelle source

1. Créer un nouveau scraper dans `scrapers/` :

```python
from scrapers.base import BaseScraper

class NewScraper(BaseScraper):
    def __init__(self):
        super().__init__("source_name")
    
    def scrape_latest(self, limit: int = 20) -> List[Dict]:
        # Scrape les articles les plus récents
        items = []
        # ... votre logique ...
        return [self.normalize_item(...) for ... in items]
    
    def scrape_all(self, limit: int = 100) -> List[Dict]:
        # Scrape tout l'historique disponible
        items = []
        # ... votre logique ...
        return [self.normalize_item(...) for ... in items]
```

2. Enregistrer le scraper dans `WatchServer._init_scrapers()` dans `main.py`

## Configuration des embeddings

Par défaut, le serveur utilise les embeddings "dummy" (aléatoires mais déterministes) pour la développement.

Pour utiliser des embeddings réels avec SentenceTransformers :

```bash
pip install sentence-transformers
```

Puis dans `main.py`, modifier le code :

```python
# Au lieu de :
if use_dummy_embeddings:
    embedding_provider = DummyEmbeddingProvider()
    
# Utiliser :
from embeddings import SentenceTransformerEmbeddingProvider
embedding_provider = SentenceTransformerEmbeddingProvider("all-MiniLM-L6-v2")
```

## Améliorations possibles

- [ ] API REST pour interroger la base de données
- [ ] Authentification/autorisation
- [ ] Pagination des résultats
- [ ] Filtrage par source, date, keywords
- [ ] Recherche sémantique avec embeddings
- [ ] Notifications pour nouveaux articles
- [ ] Déduplication plus intelligente
- [ ] Cache de résultats
- [ ] Métriques et monitoring

## Licence

Voir LICENSE
