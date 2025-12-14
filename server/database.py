"""Database manager for the server (PostgreSQL + pgvector)."""

from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Dict, List, Optional

import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row


class DatabaseManager:
    """Manages unified database operations using PostgreSQL."""

    def __init__(self, db_url: str, embedding_dimension: int = 1536):
        """Initialize the database manager and ensure schema is ready."""
        self.db_url = db_url
        self.embedding_dimension = embedding_dimension
        self.setup_database()

    @contextmanager
    def get_connection(self):
        """Context manager for PostgreSQL connections with pgvector registered."""
        conn = psycopg.connect(self.db_url, row_factory=dict_row, autocommit=False)
        register_vector(conn)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def setup_database(self):
        """Initialize database and create tables (idempotent)."""
        with self.get_connection() as conn:
            cur = conn.cursor()

            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS articles (
                    id TEXT PRIMARY KEY,
                    source_site TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    full_content TEXT,
                    content_hash TEXT UNIQUE,
                    author_info TEXT,
                    keywords TEXT,
                    content_url TEXT NOT NULL,
                    published_date TIMESTAMPTZ,
                    item_type TEXT,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id SERIAL PRIMARY KEY,
                    article_id TEXT NOT NULL UNIQUE REFERENCES articles(id) ON DELETE CASCADE,
                    embedding vector({self.embedding_dimension}) NOT NULL,
                    embedding_model TEXT,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_history (
                    id SERIAL PRIMARY KEY,
                    source_site TEXT NOT NULL,
                    sync_mode TEXT NOT NULL,
                    last_sync_time TIMESTAMPTZ,
                    items_processed INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute("CREATE INDEX IF NOT EXISTS idx_content_hash ON articles(content_hash)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_source_site ON articles(source_site)")

    def _compute_content_hash(self, item: Dict) -> str:
        import hashlib

        full_content = item.get("full_content", item.get("description", ""))
        return hashlib.sha256(full_content.encode()).hexdigest()

    def save_article(self, item: Dict, conn: Optional[psycopg.Connection] = None) -> bool:
        """Save a single article, returning True if inserted."""
        content_hash = self._compute_content_hash(item)

        if conn is None:
            with self.get_connection() as owned_conn:
                return self.save_article(item, owned_conn)

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO articles
            (id, source_site, title, description, full_content, content_hash, author_info, keywords, content_url, published_date, item_type, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                item["id"],
                item["source_site"],
                item["title"],
                item.get("description", ""),
                item.get("full_content", item.get("description", "")),
                content_hash,
                item.get("author_info", ""),
                item.get("keywords", ""),
                item["content_url"],
                item.get("published_date", datetime.now(UTC)),
                item.get("item_type", "article"),
                datetime.now(UTC),
            ),
        )

        return cur.rowcount > 0

    def save_articles_batch(self, items: List[Dict]) -> int:
        """Save multiple articles in one transaction."""
        with self.get_connection() as conn:
            count = 0
            for item in items:
                if self.save_article(item, conn):
                    count += 1
            return count

    def article_exists(self, article_id: str) -> bool:
        """Check if article already exists by ID."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM articles WHERE id = %s", (article_id,))
            return cur.fetchone() is not None

    def article_exists_by_hash(self, content_hash: str) -> bool:
        """Check if article already exists by content hash."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM articles WHERE content_hash = %s", (content_hash,))
            return cur.fetchone() is not None

    def get_article_by_hash(self, content_hash: str) -> Optional[Dict]:
        """Get article by content hash."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM articles WHERE content_hash = %s", (content_hash,))
            row = cur.fetchone()
            return dict(row) if row else None

    def save_embedding(self, article_id: str, embedding: np.ndarray, model: str = "default") -> bool:
        """Save article embedding as a pgvector."""
        if embedding.ndim != 1 or embedding.shape[0] != self.embedding_dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.embedding_dimension}, got {embedding.shape}"
            )

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO embeddings (article_id, embedding, embedding_model)
                VALUES (%s, %s, %s)
                ON CONFLICT (article_id) DO UPDATE
                SET embedding = EXCLUDED.embedding,
                    embedding_model = EXCLUDED.embedding_model,
                    created_at = CURRENT_TIMESTAMP
                """,
                (article_id, embedding.tolist(), model),
            )
            return cur.rowcount > 0

    def get_articles_without_embeddings(self, limit: int = 100) -> List[Dict]:
        """Get articles without embeddings."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT a.* FROM articles a
                LEFT JOIN embeddings e ON a.id = e.article_id
                WHERE e.id IS NULL
                LIMIT %s
                """,
                (limit,),
            )
            return list(cur.fetchall())

    def get_articles_by_source(self, source: str, limit: int = 50) -> List[Dict]:
        """Get articles from a specific source."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM articles
                WHERE source_site = %s
                ORDER BY published_date DESC NULLS LAST
                LIMIT %s
                """,
                (source, limit),
            )
            return list(cur.fetchall())

    def get_total_articles(self) -> int:
        """Return total number of articles."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS count FROM articles")
            row = cur.fetchone()
            return row["count"] if row else 0

    def get_articles_by_source_count(self) -> Dict[str, int]:
        """Return number of articles per source."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT source_site, COUNT(*) as count
                FROM articles
                GROUP BY source_site
                ORDER BY count DESC
                """
            )
            return {row["source_site"]: row["count"] for row in cur.fetchall()}

    def record_sync(self, source: str, mode: str, items_processed: int = 0):
        """Record a synchronization event."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO sync_history
                (source_site, sync_mode, last_sync_time, items_processed)
                VALUES (%s, %s, %s, %s)
                """,
                (source, mode, datetime.now(UTC), items_processed),
            )

    def get_last_sync(self, source: str, mode: str) -> Optional[Dict]:
        """Get last sync for a source and mode."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM sync_history
                WHERE source_site = %s AND sync_mode = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (source, mode),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_stats(self) -> Dict:
        """Return database statistics."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS count FROM articles")
            total_articles = cur.fetchone()["count"]

            cur.execute("SELECT COUNT(*) AS count FROM embeddings")
            total_embeddings = cur.fetchone()["count"]

            cur.execute(
                """
                SELECT source_site, COUNT(*) as count
                FROM articles
                GROUP BY source_site
                """
            )
            articles_by_source = {row["source_site"]: row["count"] for row in cur.fetchall()}

            return {
                "total_articles": total_articles,
                "total_embeddings": total_embeddings,
                "articles_by_source": articles_by_source,
                "articles_without_embeddings": total_articles - total_embeddings,
            }
