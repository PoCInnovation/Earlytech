"""Database manager for the server (PostgreSQL + pgvector)."""

from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Dict, Optional, Any, List
import json

import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from clustering.cluster_scoring import (
    compute_entity_similarity,
    compute_final_score,
)
from clustering.cluster_thresholds import (
    SEMANTIC_SIMILARITY_THRESHOLD,
    FINAL_SCORE_THRESHOLD,
)


class DatabaseManager:
    def __init__(self, db_url: str, embedding_dimension: int = 1536):
        self.db_url = db_url
        self.embedding_dimension = embedding_dimension
        self.setup_database()

    @contextmanager
    def get_connection(self):
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
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    subject TEXT,
                    organization_list JSONB,
                    event_type TEXT,
                    cluster_id INTEGER
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

            cur.execute("CREATE INDEX IF NOT EXISTS idx_cluster_id ON articles(cluster_id)")

    def assign_cluster_with_similarity(
        self,
        article_id: str,
        subject: str,
        orgs: List[str],
        event: str,
    ):
        with self.get_connection() as conn:
            cur = conn.cursor()

            cur.execute(
                """
                SELECT embedding FROM embeddings WHERE article_id = %s
                """,
                (article_id,)
            )
            row = cur.fetchone()
            if not row:
                return

            article_embedding = row["embedding"]

            cur.execute(
                """
                SELECT a.cluster_id, a.subject, a.organization_list, a.event_type,
                       1 - (e.embedding <=> %s) AS semantic_similarity
                FROM articles a
                JOIN embeddings e ON a.id = e.article_id
                WHERE a.cluster_id IS NOT NULL
                  AND (a.subject = %s OR a.event_type = %s)
                """,
                (article_embedding, subject, event),
            )

            best_cluster_id = None
            best_score = 0.0

            for row in cur.fetchall():
                semantic_score = row["semantic_similarity"]

                if semantic_score < SEMANTIC_SIMILARITY_THRESHOLD:
                    continue

                entity_score = compute_entity_similarity(
                    {
                        "subject": subject,
                        "orgs": orgs,
                        "event": event,
                    },
                    {
                        "subject": row["subject"],
                        "orgs": row["organization_list"] or [],
                        "event": row["event_type"],
                    },
                )

                final_score = compute_final_score(semantic_score, entity_score)

                if final_score > best_score:
                    best_score = final_score
                    best_cluster_id = row["cluster_id"]

            if best_cluster_id is None or best_score < FINAL_SCORE_THRESHOLD:
                cur.execute("SELECT COALESCE(MAX(cluster_id), 0) + 1 AS next_id FROM articles")
                best_cluster_id = cur.fetchone()["next_id"]

            cur.execute(
                """
                UPDATE articles
                SET subject = %s,
                    organization_list = %s::jsonb,
                    event_type = %s,
                    cluster_id = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    subject,
                    json.dumps(orgs),
                    event,
                    best_cluster_id,
                    article_id,
                ),
            )
