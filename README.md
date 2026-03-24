# EarlyTech

🚀 **Système intelligent de veille technologique avec dispatch personnalisé d'articles basé sur embeddings.**

EarlyTech scrape automatiquement des articles depuis différentes sources (arXiv, GitHub, HuggingFace, Medium, Le Monde), calcule leurs embeddings vectoriels, et dispatche intelligemment les articles aux utilisateurs en fonction de leurs mots-clés via similarité sémantique.

## 🎯 Fonctionnalités Principales

- **🔍 Multi-Source Scraping**: arXiv, GitHub, HuggingFace, Medium, Le Monde
- **🧠 Embeddings Vectoriels**: OpenAI text-embedding-3-small (1536 dimensions)
- **🎯 Matching Intelligent**: Similarité cosinus via pgvector (PostgreSQL)
- **📨 Dispatch Automatique**: Articles envoyés automatiquement aux utilisateurs (≥70% similarité)
- **🔑 Flexibilité des Keywords**: "GPT 3", "GPT-3", "GPT3" matchent tous (embeddings vs strings)
- **🦀 API REST**: Serveur Rust Axum avec 13 routes
- **📊 Statistiques**: Tracking complet des deliveries et performances

## 🏗️ Architecture

```
EarlyTech/
├── scrapper/          # Python - Scraping & Embeddings & Dispatch
│   ├── scrapers/      # Scrapers multi-sources
│   ├── clustering/    # Clustering & scoring
│   ├── database.py    # PostgreSQL + pgvector
│   ├── embeddings.py  # OpenAI embeddings
│   ├── keyword_matcher.py  # Moteur de matching
│   └── main.py        # Orchestrateur principal
│
└── server/            # Rust - API REST
    └── src/
        ├── routes.rs  # 13 routes API
        ├── handlers.rs # Business logic
        └── models.rs  # Data models
```

## 🔄 Comment Ça Marche

```
┌─────────────────┐
│  Article Scrapé │  (arXiv, GitHub, etc.)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Embedding Calculé│  OpenAI text-embedding-3-small
│ [1536 dimensions]│
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────┐
│ Comparé avec TOUS les mots-clés  │  Cosine Similarity (pgvector)
│                                  │
│ "GPT" → 92% ✅                   │
│ "transformers" → 85% ✅          │
│ "React" → 15% ❌                 │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────┐
│ Dispatch aux Users│  Si similarité ≥ 70%
│                  │
│ Article enregistré│
│ dans leurs feeds │
└──────────────────┘
```

**Technologies:**
- **Scraper**: Python 3.11+, SQLAlchemy, BeautifulSoup, OpenAI API
- **Base de données**: PostgreSQL 16+ avec pgvector
- **API Server**: Rust, Axum, SQLx, JWT
- **Embeddings**: OpenAI text-embedding-3-small
- **Matching**: Cosine similarity (threshold: 0.7)

## 🚀 Getting Started

### Prérequis

- Python 3.11+
- PostgreSQL 16+ avec extension pgvector
- Rust 1.75+
- OpenAI API Key

### Installation

#### 1. Clone le projet

```bash
git clone https://github.com/your-org/Earlytech.git
cd Earlytech
```

#### 2. Setup PostgreSQL avec pgvector

```bash
# Installer PostgreSQL et pgvector
sudo apt install postgresql-16 postgresql-16-pgvector

# Créer la database
createdb earlytech

# Activer pgvector
psql earlytech -c "CREATE EXTENSION vector;"
```

#### 3. Setup Python Scraper

```bash
cd scrapper

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp config.py.example config.py
# Éditer config.py avec vos credentials:
#   - DATABASE_URL
#   - OPENAI_API_KEY
```

#### 4. Setup Rust API Server

```bash
cd ../server

# Configurer l'environnement
cp .env.example .env
# Éditer .env:
#   - DATABASE_URL
#   - JWT_SECRET

# Compiler
cargo build --release
```

### Quickstart

#### Démarrer le Scraper (Mode Veille)

```bash
cd scrapper
python main.py watch
```

Le scraper va :
- ✅ Scraper les articles toutes les X minutes
- ✅ Calculer les embeddings automatiquement
- ✅ Dispatcher les articles aux utilisateurs
- ✅ Logger tous les matchs: `📨 Article matched to 2 user(s)`

#### Démarrer l'API Server

```bash
cd server
cargo run --release

# Serveur sur http://localhost:3000
```

#### Démo Rapide du Système de Dispatch

```bash
cd scrapper

# Demo complète interactive (~2 min)
python demo_dispatch.py

# OU script automatique
./run_demo.sh

# Vérification rapide (~10 sec)
python quick_test_dispatch.py
```

### Usage

#### 1. Créer un Utilisateur et ses Mots-clés

```bash
# Via CLI Python
cd scrapper
python examples_user_keywords.py setup

# OU via API REST
curl -X POST http://localhost:3000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","password":"secure123"}'

curl -X POST http://localhost:3000/users/<USER_ID>/keywords \
  -H "Content-Type: application/json" \
  -d '{"keyword":"GPT"}'
```

#### 2. Voir le Feed Personnalisé

```bash
# Via CLI
python examples_user_keywords.py feed <USER_ID>

# Via API
curl http://localhost:3000/users/<USER_ID>/feed
```

#### 3. Statistiques

```bash
# Stats utilisateur
curl http://localhost:3000/users/<USER_ID>/stats

# Stats globales
curl http://localhost:3000/delivery/stats

# Monitoring en temps réel
python monitor_dispatch.py monitor
```

## 🧪 Tests

### Tests Scraper Python

```bash
cd scrapper

# Tests unitaires (8 tests)
python tests_keyword_matcher.py

# Vérification rapide
python quick_test_dispatch.py

# Demo complète
python demo_dispatch.py
```

### Tests Server Rust

```bash
cd server

# Vérification compilation
cargo check

# Compilation
cargo build

# Tests (à venir)
cargo test
```

## 🎯 Routes API Disponibles

| Méthode | Route | Description |
|---------|-------|-------------|
| **Articles** |||
| GET | `/articles` | Liste des articles |
| GET | `/articles/:id` | Détails d'un article |
| GET | `/articles/count` | Nombre d'articles |
| **Auth** |||
| POST | `/auth/register` | Créer un compte |
| POST | `/auth/login` | Se connecter (JWT) |
| **Keywords** |||
| GET | `/users/:id/keywords` | Liste des keywords |
| POST | `/users/:id/keywords` | Ajouter un keyword |
| DELETE | `/users/:user_id/keywords/:keyword_id` | Supprimer un keyword |
| **Preferences** |||
| GET | `/users/:id/preferences` | Récupérer les préférences digest |
| POST | `/users/:id/preferences` | Mettre à jour les préférences digest |
| **Exclusions** |||
| GET | `/users/:id/exclusions` | Liste des exclusions (sources + keywords) |
| POST | `/users/:id/exclusions/sources` | Exclure une source |
| DELETE | `/users/:user_id/exclusions/sources/:source` | Retirer une source exclue |
| POST | `/users/:id/exclusions/keywords` | Exclure un keyword |
| DELETE | `/users/:user_id/exclusions/keywords/:keyword_id` | Retirer un keyword exclu |
| **Feed** |||
| GET | `/users/:id/feed` | Feed personnalisé |
| **Feedback** |||
| POST | `/users/:id/feedback` | Enregistrer le feedback (relevant / not_relevant) |
| **Stats** |||
| GET | `/users/:id/stats` | Stats utilisateur |
| GET | `/users/:id/quality` | Dashboard qualité des recommandations |
| GET | `/delivery/stats` | Stats globales |
| GET | `/delivery/recent` | Deliveries récentes |

Voir [server/API.md](server/API.md) pour la documentation complète avec exemples.

## 📊 Base de Données

### Tables Principales

```sql
-- Utilisateurs & Keywords
users                       -- Comptes utilisateurs
user_keywords               -- Mots-clés centralisés
user_keyword_embeddings     -- Embeddings des keywords

-- Articles
articles                    -- Articles scrapés
article_embeddings          -- Embeddings des articles

-- Dispatch
user_article_delivery       -- Historique des dispatches

-- Clustering (optionnel)
article_clusters            -- Clusters d'articles
entity_extractions          -- Entités extraites
```

## 🔧 Scripts Utilitaires

```bash
# Setup users et keywords de démo
python examples_user_keywords.py setup

# Voir le feed d'un user
python examples_user_keywords.py feed <user_id>

# Tester le matching d'un article
python examples_user_keywords.py match <article_id>

# Stats d'un user
python examples_user_keywords.py stats <user_id>

# Monitoring temps réel
python monitor_dispatch.py monitor

# Stats globales
python monitor_dispatch.py stats

# 20 dernières deliveries
python monitor_dispatch.py recent
```

## 🎨 Exemples

### Exemple de Workflow Complet

```bash
# 1. Démarrer le scraper en mode watch
python main.py watch &

# 2. Créer des users avec keywords
python examples_user_keywords.py setup

# 3. Observer les dispatches dans les logs
# Output: 📨 Article matched to 2 user(s)

# 4. Voir le feed d'un user
python examples_user_keywords.py feed 1

# Output:
# ✉️  arxiv_2403.12345 - "GPT-5 Released" (92% match via 'gpt')
# ✉️  arxiv_2403.45678 - "Transformers Evolution" (88% match via 'transformers')
```

## 📈 Performance

- **Scraping**: ~100 articles/minute (multi-sources)
- **Embeddings**: ~50 articles/seconde (batch OpenAI)
- **Matching**: <100ms pour 1000 keywords (pgvector index)
- **API**: <10ms latence moyenne

## 🔒 Sécurité

- ✅ Mots de passe hashés avec Argon2
- ✅ JWT tokens (expiration 60 min)
- ✅ Protection SQL injection (paramètres liés)
- ✅ Validation des inputs
- ✅ HTTPS recommandé en production

## 🐛 Troubleshooting

### Erreur: "pgvector extension not found"
```bash
psql earlytech -c "CREATE EXTENSION vector;"
```

### Erreur: "OpenAI API key invalid"
```bash
# Vérifier config.py
OPENAI_API_KEY = "sk-..."
```

### Erreur: "Database connection failed"
```bash
# Vérifier PostgreSQL
sudo systemctl status postgresql
```

## 🚀 Production

### Recommendations

1. **Environment Variables**: Ne jamais commit les API keys
2. **HTTPS**: Utiliser un reverse proxy (nginx/traefik)
3. **Monitoring**: Logs centralisés (ELK, Datadog)
4. **Backups**: PostgreSQL automatiques quotidiens
5. **Rate Limiting**: Protéger l'API
6. **Scaling**: Connection pooling, caching Redis

## Get involved

You're invited to join this project ! Check out the [contributing guide](./CONTRIBUTING.md).

If you're interested in how the project is organized at a higher level, please contact the current project manager.

## Our PoC team ❤️

Developers
| [<img src="https://github.com/MrZalTy.png?size=85" width=85><br><sub>[Developer's name]</sub>](https://github.com/MrZalTy) | [<img src="https://github.com/MrZalTy.png?size=85" width=85><br><sub>[Developer's name]</sub>](https://github.com/MrZalTy) | [<img src="https://github.com/MrZalTy.png?size=85" width=85><br><sub>[Developer's name]</sub>](https://github.com/MrZalTy)
| :---: | :---: | :---: |

Manager
| [<img src="https://github.com/adrienfort.png?size=85" width=85><br><sub>[Manager's name]</sub>](https://github.com/adrienfort)
| :---: |

<h2 align=center>
Organization
</h2>

<p align='center'>
    <a href="https://www.linkedin.com/company/pocinnovation/mycompany/">
        <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn logo">
    </a>
    <a href="https://www.instagram.com/pocinnovation/">
        <img src="https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white" alt="Instagram logo"
>
    </a>
    <a href="https://twitter.com/PoCInnovation">
        <img src="https://img.shields.io/badge/Twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white" alt="Twitter logo">
    </a>
    <a href="https://discord.com/invite/Yqq2ADGDS7">
        <img src="https://img.shields.io/badge/Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white" alt="Discord logo">
    </a>
</p>
<p align=center>
    <a href="https://www.poc-innovation.fr/">
        <img src="https://img.shields.io/badge/WebSite-1a2b6d?style=for-the-badge&logo=GitHub Sponsors&logoColor=white" alt="Website logo">
    </a>
</p>

> 🚀 Don't hesitate to follow us on our different networks, and put a star 🌟 on `PoC's` repositories

> Made with ❤️ by PoC