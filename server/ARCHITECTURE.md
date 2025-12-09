# Watch Server - Complete Redesign

## 📋 Summary of Changes

The server has been completely redesigned with a modular architecture and two clearly defined operating modes.

## 🏗️ Architecture

```
server/
├── main.py                 # Main server with WatchServer (orchestrator)
├── database.py             # SQLite database manager
├── embeddings.py           # Embeddings manager (vectors)
├── config.py              # Centralized configuration
├── examples.py            # Usage examples
├── requirements.txt       # Python dependencies
├── README.md              # Complete documentation
└── scrapers/
    ├── base.py            # Abstract BaseScraper interface
    ├── arxiv_scraper.py    # Scraper for arXiv
    ├── github_scraper.py   # Scraper for GitHub
    ├── medium_scraper.py   # Scraper for Medium
    ├── lemonde_scraper.py  # Scraper for Le Monde
    └── huggingface_scraper.py # Scraper for Hugging Face
```

## 🎯 Two Operating Modes

### 1️⃣ Backfill Mode (History)
**When:** At server startup

**What:** Scrapes all available history from each source

**How:**
```bash
python main.py backfill --limit 100
```

**Flow:**
1. Scraper calls `scrape_all()` for each source
2. Articles are saved to DB (deduplicated by ID)
3. Embeddings generated and stored for each article
4. Sync recorded in `sync_history`

### 2️⃣ Watch Mode (Monitoring)
**When:** After backfill or directly

**What:** Continuously scrapes new articles

**How:**
```bash
python main.py watch --interval 300
```

**Flow:**
1. Infinite loop (by default, checks every 5 min)
2. Scraper calls `scrape_latest()` for each source
3. New articles detected (ID comparison)
4. Save and create embeddings
5. Wait for next interval

## 🔧 Main Components

### BaseScraper (abstract interface)
All scrapers inherit from this class and implement:
- `scrape_latest(limit)` → for watch mode
- `scrape_all(limit)` → for backfill mode
- `normalize_item()` → unified format

### DatabaseManager
- Manages SQLite persistence
- Tables: articles, embeddings, sync_history
- Automatic deduplication (INSERT OR IGNORE)
- Batch operations for performance

### EmbeddingManager
- Support for multiple providers (Dummy, SentenceTransformers)
- Vector serialization/deserialization
- Storage as BLOB in DB

### WatchServer (orchestrator)
- Initializes all scrapers
- Manages both modes
- Detailed operation logging
- Statistics and monitoring

## 💾 Database Structure

### Table `articles`
```
id (TEXT PRIMARY KEY)      # Unique identifier per source
source_site (TEXT)         # arxiv, github, medium, le_monde, huggingface
title (TEXT)              # Article title
description (TEXT)        # Summary/content
author_info (TEXT)        # Author(s)
keywords (TEXT)           # Tags/categories
content_url (TEXT)        # Link to source
published_date (TEXT)     # Publication date
item_type (TEXT)          # article, paper, repository, etc.
created_at (TIMESTAMP)    # When we retrieved it
updated_at (TIMESTAMP)    # Last update
```

### Table `embeddings`
```
article_id (TEXT UNIQUE)  # Link to articles.id
embedding (BLOB)          # Serialized vector (pickle)
embedding_model (TEXT)    # Which model generated the embedding
created_at (TIMESTAMP)    # When created
```

### Table `sync_history`
```
source_site (TEXT)        # Which source
sync_mode (TEXT)          # "watch" or "backfill"
last_sync_time (TIMESTAMP) # When
items_processed (INTEGER) # How many articles
```

## 🚀 Usage

### Simple startup
```bash
# 1. Fill DB with history
python main.py backfill --limit 50

# 2. Then monitor continuously
python main.py watch --interval 300

# 3. Check stats
python main.py stats
```

### With options
```bash
# Custom backfill
python main.py backfill --limit 200 --db custom.db

# Watch with 10 min interval
python main.py watch --interval 600

# Stats on specific DB
python main.py stats --db custom.db
```

## 📊 Complete Flow Example

```
Server startup
│
├─→ BACKFILL Mode (optional)
│   ├─→ ArXiv.scrape_all(100)    → 45 articles → DB
│   ├─→ GitHub.scrape_all(100)   → 78 articles → DB
│   ├─→ Medium.scrape_all(100)   → 23 articles → DB
│   ├─→ LeMonde.scrape_all(100)  → 67 articles → DB
│   └─→ HF.scrape_all(100)       → 89 articles → DB
│       ↓ All articles receive an embedding
│       → 302 articles in DB with embeddings
│
└─→ WATCH Mode (infinite loop)
    ├─→ Iteration 1
    │   ├─→ ArXiv.scrape_latest(20)   → 2 new
    │   ├─→ GitHub.scrape_latest(20)  → 1 new
    │   ├─→ Medium.scrape_latest(20)  → 0 new
    │   ├─→ LeMonde.scrape_latest(20) → 1 new
    │   └─→ HF.scrape_latest(20)      → 2 new
    │       → 6 new articles added
    │
    ├─→ [Wait 5 min]
    │
    └─→ Iteration 2
        └─→ ...
```

## 🔑 Key Design Points

### ✓ Modularity
- Each scraper is independent
- Easy to add/remove a source
- Interchangeable embedding providers

### ✓ Robustness
- Error handling per scraper
- No interruption if a source fails
- Automatic deduplication

### ✓ Scalability
- Batch operations for DB
- Context manager for connections
- Logging for monitoring

### ✓ Maintainability
- Clear and documented code
- Centralized configuration
- Usage examples

## 💻 How to View the Database

### Option 1: Export and View Locally
```bash
# Export database to local .db file
python main.py export --db veille_technique.db --output veille_export.db

# View with SQLite Browser or VSCode extension
# Export creates a complete copy of the DB
```

### Option 2: Use sqlite3 from Command Line
```bash
# Open the database
sqlite3 veille_technique.db

# Some useful queries
sqlite> SELECT COUNT(*) FROM articles;  -- Total articles
sqlite> SELECT source_site, COUNT(*) FROM articles GROUP BY source_site;  -- By source
sqlite> SELECT * FROM articles LIMIT 5;  -- View first 5 articles
sqlite> SELECT source_site, COUNT(*) FROM embeddings GROUP BY source_site;  -- Embeddings per source
```

### Option 3: Use a GUI
- **SQLite Browser**: `brew install sqlitebrowser` (macOS) or `apt install sqlitebrowser` (Linux)
- **VSCode Extension**: "SQLite" extension (officially supported)
- **DBeaver Community**: Free multi-DB application

### Example: View Articles from One Source
```bash
sqlite3 veille_technique.db << EOF
.headers on
.mode column
SELECT title, author_info, published_date FROM articles 
WHERE source_site = 'github' 
ORDER BY published_date DESC 
LIMIT 10;
EOF
```

### Complete DB Structure
```bash
# View all tables
sqlite3 veille_technique.db ".tables"

# View schema of a table
sqlite3 veille_technique.db ".schema articles"

# View sync stats
sqlite3 veille_technique.db "SELECT * FROM sync_history ORDER BY created_at DESC LIMIT 5;"
```

## 📝 Migration from Old Server

Old code in the `scrap/` folder remains untouched for reference.
The new server reuses the scraping logic but with a completely restructured architecture.
