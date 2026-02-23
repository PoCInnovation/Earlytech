# Scrapper Startup Guide

This guide explains how to launch the technical watch scrapper system.

## Prerequisites

- **Python 3.9+**
- **PostgreSQL** with **pgvector** extension
- **OpenAI API Key** (for embeddings and entity extraction)
- **(Optional)** GitHub Token for higher rate limits

## Installation

### 1. Create a Python Virtual Environment

```bash
cd scrapper
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup PostgreSQL with pgvector

Install PostgreSQL and the pgvector extension:

```bash
# On Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE EXTENSION vector;"

# Or using Docker
docker run -d \
  --name postgres-pgvector \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=veille_technique \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### 4. Configure Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` and set your credentials:

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/veille_technique
EMBEDDING_MODEL=text-embedding-3-small
GITHUB_TOKEN=your_github_token_here  # Optional
```

### 5. Initialize the Database

The database schema will be created automatically on first run.

## Running the Scrapper

The scrapper has **3 modes**:

### 1. Backfill Mode (Historical Data)

Scrape entire available history from all sources:

```bash
python main.py backfill
```

Options:
- `--limit N` - Maximum articles per source (default: 100)
- `--db-url URL` - Override database URL
- `--embedding-model MODEL` - Override embedding model
- `--llm-model MODEL` - Override LLM model for entities

Example with custom limit:
```bash
python main.py backfill --limit 200
```

### 2. Watch Mode (Continuous Monitoring)

Scrape new articles continuously at regular intervals:

```bash
python main.py watch
```

Options:
- `--interval SECONDS` - Scraping interval (default: 300s = 5 minutes)
- `--db-url URL` - Override database URL
- `--embedding-model MODEL` - Override embedding model
- `--llm-model MODEL` - Override LLM model for entities

Example with 10-minute interval:
```bash
python main.py watch --interval 600
```

Press `Ctrl+C` to stop the watch mode.

### 3. Stats Mode (View Statistics)

Display database statistics:

```bash
python main.py stats
```

## Available Scrapers

The system includes scrapers for:

- **ArXiv** - Scientific papers (cs.LG category by default)
- **GitHub** - Trending repositories
- **Medium** - Technical articles
- **Le Monde** - News articles
- **Hugging Face** - ML models and papers

## Features

Each scraped article is automatically:
1. **Deduplicated** - By ID and content hash
2. **Embedded** - Using OpenAI embeddings (for similarity search)
3. **Analyzed** - Entities extracted via LLM (technologies, companies, people, etc.)

## Configuration

### Database Connection

Set via environment variable or command-line:
- Environment: `DATABASE_URL=postgresql://user:pass@host:port/dbname`
- CLI: `--db-url postgresql://user:pass@host:port/dbname`

### Embedding Model

Configure the OpenAI embedding model:
- Environment: `EMBEDDING_MODEL=text-embedding-3-small`
- CLI: `--embedding-model text-embedding-3-small`

Available models:
- `text-embedding-3-small` (1536 dimensions, faster)
- `text-embedding-3-large` (3072 dimensions, more accurate)

### LLM Model

Configure the LLM for entity extraction:
- Environment: `LLM_MODEL=gpt-4o-mini`
- CLI: `--llm-model gpt-4o-mini`

## Troubleshooting

### Missing OpenAI API Key

```
Error: OpenAI API key not found
```

**Solution**: Set `OPENAI_API_KEY` in your `.env` file.

### PostgreSQL Connection Error

```
Error: could not connect to server
```

**Solution**: 
1. Check PostgreSQL is running: `sudo systemctl status postgresql`
2. Verify DATABASE_URL in `.env`
3. Ensure pgvector extension is installed

### Scraper Initialization Failed

If a scraper fails to initialize, it will be skipped automatically. Check the logs for details.

### Port Already in Use (PostgreSQL)

If port 5432 is already used, either:
1. Stop the conflicting service
2. Use a different port in `DATABASE_URL`

## Development Tips

### Check Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for system design details.

### Database Management

View articles directly in PostgreSQL:
```sql
-- Connect to database
psql $DATABASE_URL

-- Count articles
SELECT COUNT(*) FROM articles;

-- View recent articles
SELECT title, source, published_at FROM articles 
ORDER BY published_at DESC LIMIT 10;

-- Check embeddings
SELECT COUNT(*) FROM embeddings;
```

## Recommended Workflow

1. **Initial setup**: Run `backfill` mode once to populate historical data
2. **Continuous monitoring**: Run `watch` mode to keep data up-to-date
3. **Check progress**: Use `stats` mode to monitor collection

Example:
```bash
# One-time: populate history
python main.py backfill --limit 50

# Continuous: monitor new content
python main.py watch --interval 600

# Anytime: check statistics
python main.py stats
```
