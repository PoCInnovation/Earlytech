"""Database manager for the server (PostgreSQL + pgvector)."""

from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Dict, List, Optional, Tuple, Any

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
                """
                ALTER TABLE articles 
                ADD COLUMN IF NOT EXISTS subject TEXT,
                ADD COLUMN IF NOT EXISTS organization_list JSONB, 
                ADD COLUMN IF NOT EXISTS event_type TEXT,
                ADD COLUMN IF NOT EXISTS cluster_id INTEGER 
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
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cluster_id ON articles(cluster_id)")

    def _compute_content_hash(self, item: Dict) -> str:
        import hashlib
        full_content = item.get("full_content", item.get("description", ""))
        return hashlib.sha256(full_content.encode()).hexdigest()

    def save_article(self, item: Dict, conn: Optional[psycopg.Connection] = None) -> bool:
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

    def article_exists(self, article_id: str) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM articles WHERE id = %s", (article_id,))
            return cur.fetchone() is not None

    def article_exists_by_hash(self, content_hash: str) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM articles WHERE content_hash = %s", (content_hash,))
            return cur.fetchone() is not None

    def save_embedding(self, article_id: str, embedding: np.ndarray, model: str = "default") -> bool:
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

    def assign_cluster_by_entities(self, article_id: str, subject: str, orgs: str, event: str):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT cluster_id FROM articles 
                WHERE subject = %s AND organization_list = %s::jsonb AND event_type = %s 
                AND cluster_id IS NOT NULL LIMIT 1
                """,
                (subject, orgs, event)
            )
            row = cur.fetchone()
            if row:
                cid = row['cluster_id']
            else:
                cur.execute("SELECT COALESCE(MAX(cluster_id), 0) + 1 as next_id FROM articles")
                cid = cur.fetchone()['next_id']
            
            cur.execute(
                """
                UPDATE articles SET subject=%s, organization_list=%s::jsonb, 
                event_type=%s, cluster_id=%s, updated_at=CURRENT_TIMESTAMP 
                WHERE id=%s
                """,
                (subject, orgs, event, cid, article_id)
            )

    def get_stats(self) -> Dict:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS count FROM articles")
            total_articles = cur.fetchone()["count"]
            cur.execute("SELECT COUNT(*) AS count FROM embeddings")
            total_embeddings = cur.fetchone()["count"]
            cur.execute("SELECT COUNT(DISTINCT cluster_id) AS count FROM articles WHERE cluster_id IS NOT NULL")
            total_clusters = cur.fetchone()["count"]
            cur.execute("SELECT source_site, COUNT(*) as count FROM articles GROUP BY source_site")
            articles_by_source = {row["source_site"]: row["count"] for row in cur.fetchall()}
            return {
                "total_articles": total_articles,
                "total_embeddings": total_embeddings,
                "articles_by_source": articles_by_source,
                "articles_without_embeddings": total_articles - total_embeddings,
                "total_clusters": total_clusters,
            }

    def record_sync(self, source: str, mode: str, items_processed: int = 0):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO sync_history (source_site, sync_mode, last_sync_time, items_processed) VALUES (%s, %s, %s, %s)",
                (source, mode, datetime.now(UTC), items_processed),
            )