# Watch Server - Complete Redesign

## 📋 Summary of Changes

The server has been redesigned with a modular architecture and two operating modes.

## 🏗️ Architecture

```
server/
├── main.py                 # Main server with WatchServer (orchestrator)
├── database.py             # PostgreSQL + pgvector database manager
├── embeddings.py           # Embeddings manager (vectors)
├── config.py               # Centralized configuration
├── examples.py             # Usage examples
├── requirements.txt        # Python dependencies
├── README.md               # Complete documentation
└── scrapers/
    ├── base.py             # Abstract BaseScraper interface
    ├── arxiv_scraper.py     # Scraper for arXiv
    ├── github_scraper.py    # Scraper for GitHub
    ├── medium_scraper.py    # Scraper for Medium
    ├── lemonde_scraper.py   # Scraper for Le Monde
    └── huggingface_scraper.py # Scraper for Hugging Face
```

## 🎯 Operating Modes

### 1️⃣ Backfill Mode (History)
**When:** At startup (optional)

**What:** Scrapes all available history from each source.

**How:**
```bash
python main.py backfill --limit 100
```

**Flow:**
1. Each scraper calls `scrape_all()`.
2. Articles are saved (deduplicated by ID and hash).
3. Embeddings are generated and stored.
4. Sync history is recorded.

### 2️⃣ Watch Mode (Monitoring)
**When:** Continuous monitoring after (or without) backfill.

**How:**
```bash
python main.py watch --interval 300
```

**Flow:**
1. Infinite loop (default 5-minute interval).
2. Each scraper calls `scrape_latest()`.
3. New articles are saved; embeddings generated.
4. Sync history is recorded.

## 🔧 Main Components

### BaseScraper (abstract interface)
- `scrape_latest(limit)` → watch mode
- `scrape_all(limit)` → backfill mode
- `normalize_item()` → unified format

### DatabaseManager
- PostgreSQL persistence with pgvector
- Tables: articles, embeddings (vector), sync_history
- Automatic deduplication via `ON CONFLICT`
- Vector-ready queries and batch operations

### EmbeddingManager
- Providers: Dummy, SentenceTransformers, OpenAI
- Generates numpy vectors sized to the chosen model
- Stores vectors directly in pgvector columns (no pickle)

### WatchServer (orchestrator)
- Initializes all scrapers
- Manages both modes
- Logging, statistics, and monitoring

## 💾 Database Structure

### Table `articles`
```
id (TEXT PRIMARY KEY)      # Unique identifier per source
source_site (TEXT)         # arxiv, github, medium, le_monde, huggingface
title (TEXT)               # Article title
description (TEXT)         # Summary/content
author_info (TEXT)         # Author(s)
keywords (TEXT)            # Tags/categories
content_url (TEXT)         # Link to source
published_date (TIMESTAMPTZ) # Publication date
item_type (TEXT)           # article, paper, repository, etc.
created_at (TIMESTAMPTZ)   # When retrieved
updated_at (TIMESTAMPTZ)   # Last update
```

### Table `embeddings`
```
id (SERIAL PRIMARY KEY)         # Unique embedding row
article_id (TEXT UNIQUE)        # Link to articles.id
embedding vector(1536)          # pgvector column (dimension tied to embedding model)
embedding_model (TEXT)          # Which model generated the embedding
created_at (TIMESTAMPTZ)        # When created
```

### Table `sync_history`
```
id (SERIAL PRIMARY KEY)         # Unique sync row
source_site (TEXT)              # Which source
sync_mode (TEXT)                # "watch" or "backfill"
last_sync_time (TIMESTAMPTZ)    # When
items_processed (INTEGER)       # How many articles
created_at (TIMESTAMPTZ)        # When recorded
```

## 🚀 Usage

### Simple startup
```bash
# 1. Fill DB with history
python main.py backfill --limit 50

# 2. Monitor continuously
python main.py watch --interval 300

# 3. Check stats
python main.py stats
```

### With options
```bash
# Custom backfill
python main.py backfill --limit 200 --db-url postgresql://user:pass@localhost:5432/veille_technique

# Watch with 10-minute interval
python main.py watch --interval 600

# Stats on specific DB
python main.py stats --db-url postgresql://user:pass@localhost:5432/veille_technique
```

## 📊 Complete Flow Example

```
Server startup
│
├─→ BACKFILL Mode (optional)
│   ├─→ ArXiv.scrape_all(100)    → … articles → DB
│   ├─→ GitHub.scrape_all(100)   → … articles → DB
│   ├─→ Medium.scrape_all(100)   → … articles → DB
│   ├─→ LeMonde.scrape_all(100)  → … articles → DB
│   └─→ HF.scrape_all(100)       → … articles → DB
│       ↓ All articles receive an embedding
│
└─→ WATCH Mode (infinite loop)
    ├─→ Iteration 1 …
    ├─→ [Wait interval]
    └─→ Iteration 2 …
```

## 🔑 Key Design Points

### ✓ Modularity
- Independent scrapers; easy to add/remove
- Interchangeable embedding providers

### ✓ Robustness
- Error isolation per scraper
- Deduplication prevents duplicates

### ✓ Scalability
- Batch DB operations
- Vector-ready schema
- Structured logging

### ✓ Maintainability
- Clear code and docs
- Centralized configuration
- Usage examples included

## 💻 How to View the Database

Use PostgreSQL tooling (`psql`, `pgcli`, DBeaver, PgAdmin`) with `DATABASE_URL`.

```bash
# List tables
psql "$DATABASE_URL" -c "\dt"

# Check pgvector extension
psql "$DATABASE_URL" -c "\dx vector"

# Quick counts
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM articles;"
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM embeddings;"

# Example vector query (top 5 nearest)
psql "$DATABASE_URL" -c "SELECT article_id, embedding <-> '[0.1,0.2,...]' AS distance FROM embeddings ORDER BY embedding <-> '[0.1,0.2,...]' LIMIT 5;"

# Last syncs
psql "$DATABASE_URL" -c "SELECT * FROM sync_history ORDER BY created_at DESC LIMIT 5;"

# Export (custom format)
pg_dump --dbname="$DATABASE_URL" --format=c --file=veille_technique.dump
```

## 📝 Migration from Old Server

Legacy code in `scrap/` remains for reference; the new server reuses scraping logic with the updated architecture.
