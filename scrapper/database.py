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
from cross_encoder import CrossEncoderManager


class DatabaseManager:
    def __init__(self, db_url: str, embedding_dimension: int = 1536):
        self.db_url = db_url
        self.embedding_dimension = embedding_dimension
        self.cross_encoder = CrossEncoderManager()
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
                    primary_subject TEXT,
                    secondary_subject TEXT,
                    primary_organizations JSONB,
                    secondary_organizations JSONB,
                    primary_event_type TEXT,
                    secondary_event_type TEXT,
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
        primary_subject: str,
        secondary_subject: str,
        primary_orgs: List[str],
        secondary_orgs: List[str],
        primary_event: str,
        secondary_event: str,
        article_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Assign article to a cluster using semantic similarity (cross-encoder) and entity matching.
        
        Args:
            article_id: The article ID
            primary_subject: Primary subject extracted by LLM
            secondary_subject: Secondary subject extracted by LLM
            primary_orgs: Primary organizations from LLM
            secondary_orgs: Secondary organizations from LLM
            primary_event: Primary event type from LLM
            secondary_event: Secondary event type from LLM
            article_data: Full article data for cross-encoder (title, description, etc.)
        """
        with self.get_connection() as conn:
            cur = conn.cursor()

            # Get article data if not provided
            if article_data is None:
                cur.execute(
                    """
                    SELECT id, title, description, full_content
                    FROM articles WHERE id = %s
                    """,
                    (article_id,)
                )
                article_data = cur.fetchone()
                if not article_data:
                    return

            # Fetch candidate articles from clusters
            cur.execute(
                """
                SELECT a.id, a.cluster_id, a.title, a.description,
                       a.primary_subject, a.secondary_subject,
                       a.primary_event_type, a.secondary_event_type,
                       a.primary_organizations, a.secondary_organizations,
                       1 - (e.embedding <=> 
                           (SELECT embedding FROM embeddings WHERE article_id = %s)
                       ) AS embedding_similarity
                FROM articles a
                JOIN embeddings e ON a.id = e.article_id
                WHERE a.cluster_id IS NOT NULL
                  AND a.id != %s
                ORDER BY embedding_similarity DESC
                LIMIT 20
                """,
                (article_id, article_id),
            )

            candidate_rows = cur.fetchall()
            if not candidate_rows:
                # No clusters exist yet, create new cluster
                cur.execute("SELECT COALESCE(MAX(cluster_id), 0) + 1 AS next_id FROM articles")
                best_cluster_id = cur.fetchone()["next_id"]
            else:
                best_cluster_id = None
                best_score = 0.0

                # Compute cross-encoder scores for all candidates
                cross_encoder_scores = self.cross_encoder.compute_batch_relevance_scores(
                    article_data,
                    candidate_rows
                )

                for row, cross_score in zip(candidate_rows, cross_encoder_scores):
                    # Skip if embedding similarity is too low
                    embedding_sim = row["embedding_similarity"]
                    if embedding_sim < SEMANTIC_SIMILARITY_THRESHOLD:
                        continue

                    # Compute entity similarity with priority to primary entities
                    entity_score = compute_entity_similarity(
                        {
                            "primary_subject": primary_subject,
                            "secondary_subject": secondary_subject,
                            "primary_orgs": primary_orgs,
                            "secondary_orgs": secondary_orgs,
                            "primary_event": primary_event,
                            "secondary_event": secondary_event,
                        },
                        {
                            "primary_subject": row["primary_subject"],
                            "secondary_subject": row["secondary_subject"],
                            "primary_orgs": row["primary_organizations"] or [],
                            "secondary_orgs": row["secondary_organizations"] or [],
                            "primary_event": row["primary_event_type"],
                            "secondary_event": row["secondary_event_type"],
                        },
                    )

                    # Combine scores: embedding (0.3), cross-encoder (0.3), entity (0.4)
                    final_score = (
                        0.3 * embedding_sim +
                        0.3 * cross_score +
                        0.4 * entity_score
                    )

                    if final_score > best_score:
                        best_score = final_score
                        best_cluster_id = row["cluster_id"]

                # Check if score meets threshold
                if best_score < FINAL_SCORE_THRESHOLD:
                    cur.execute("SELECT COALESCE(MAX(cluster_id), 0) + 1 AS next_id FROM articles")
                    best_cluster_id = cur.fetchone()["next_id"]

            # Update article with cluster assignment and entities
            cur.execute(
                """
                UPDATE articles
                SET primary_subject = %s,
                    secondary_subject = %s,
                    primary_organizations = %s::jsonb,
                    secondary_organizations = %s::jsonb,
                    primary_event_type = %s,
                    secondary_event_type = %s,
                    cluster_id = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    primary_subject,
                    secondary_subject,
                    json.dumps(primary_orgs),
                    json.dumps(secondary_orgs),
                    primary_event,
                    secondary_event,
                    best_cluster_id,
                    article_id,
                ),
            )

