"""Initialise la base de données : crée l'extension pgvector (vector) et la table `articles`.

Usage:
    python -m server_scrappe.db.init_db
Ou depuis le dossier racine du projet.
"""
from server_scrappe.db.connection import get_connection


DDL_WITH_VECTOR = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    summary TEXT,
    tags TEXT[],
    keywords TEXT[],
    full_text TEXT NOT NULL,
    pdf_path TEXT,
    source TEXT,
    source_url TEXT,
    author TEXT,
    published_at TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT NOW(),
    embedding vector(1536),
    cluster_id INT,
    confidence_score FLOAT,
    notified BOOLEAN DEFAULT FALSE,
    notification_sent_at TIMESTAMP,
    UNIQUE(source, source_url)
);
"""

DDL_NO_VECTOR = """
CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    summary TEXT,
    tags TEXT[],
    keywords TEXT[],
    full_text TEXT NOT NULL,
    pdf_path TEXT,
    source TEXT,
    source_url TEXT,
    author TEXT,
    published_at TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT NOW(),
    embedding_json JSONB,
    cluster_id INT,
    confidence_score FLOAT,
    notified BOOLEAN DEFAULT FALSE,
    notification_sent_at TIMESTAMP,
    UNIQUE(source, source_url)
);
"""


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    try:
        print("[db.init] Trying to create extension 'vector' and table with vector column...")
        try:
            cur.execute(DDL_WITH_VECTOR)
            conn.commit()
            print("[db.init] Created/ensured table with 'vector' embedding column.")
            return
        except Exception as e:
            conn.rollback()
            print(f"[db.init] Could not create vector extension/table (fallback). Reason: {e}")
            print("[db.init] Creating table without vector (using embedding_json JSONB)...")
            cur.execute(DDL_NO_VECTOR)
            conn.commit()
            print("[db.init] Created/ensured table without vector column.")
            return
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    init_db()
