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

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT UNIQUE,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_keywords (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    keyword TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, keyword)
                )
                """
            )

            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS user_keyword_embeddings (
                    id SERIAL PRIMARY KEY,
                    keyword_id INTEGER NOT NULL UNIQUE REFERENCES user_keywords(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    keyword TEXT NOT NULL,
                    embedding vector({self.embedding_dimension}) NOT NULL,
                    embedding_model TEXT,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_article_delivery (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    article_id TEXT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                    keyword_id INTEGER REFERENCES user_keywords(id) ON DELETE SET NULL,
                    similarity_score FLOAT NOT NULL,
                    delivered_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, article_id)
                )
                """
            )

            cur.execute("CREATE INDEX IF NOT EXISTS idx_user_keywords ON user_keywords(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_keyword_embeddings ON user_keyword_embeddings(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_user_article_delivery ON user_article_delivery(user_id)")

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

    # USER AND KEYWORD FILTERING METHODS :

    def add_user(self, username: str, email: Optional[str] = None) -> int:
        """
        Add a new user to the system.
        
        Args:
            username: Unique username
            email: Optional email address
            
        Returns:
            User ID
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO users (username, email)
                VALUES (%s, %s)
                ON CONFLICT (username) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                (username, email),
            )
            user_id = cur.fetchone()["id"]
            return user_id

    def add_user_keyword(self, user_id: int, keyword: str) -> int:
        """
        Add a keyword for a user (without embedding yet).
        
        Args:
            user_id: User ID
            keyword: Keyword text
            
        Returns:
            Keyword ID
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO user_keywords (user_id, keyword)
                VALUES (%s, %s)
                ON CONFLICT (user_id, keyword) DO UPDATE SET created_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                (user_id, keyword),
            )
            keyword_id = cur.fetchone()["id"]
            return keyword_id

    def store_keyword_embedding(
        self, 
        keyword_id: int, 
        user_id: int,
        keyword: str,
        embedding: np.ndarray, 
        embedding_model: str = "text-embedding-3-small"
    ) -> None:
        """
        Store embedding for a user keyword.
        
        Args:
            keyword_id: Keyword ID
            user_id: User ID
            keyword: Keyword text
            embedding: Numpy embedding vector
            embedding_model: Model used for embedding
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                INSERT INTO user_keyword_embeddings (keyword_id, user_id, keyword, embedding, embedding_model)
                VALUES (%s, %s, %s, %s::vector, %s)
                ON CONFLICT (keyword_id) DO UPDATE 
                SET embedding = EXCLUDED.embedding, embedding_model = EXCLUDED.embedding_model
                """,
                (keyword_id, user_id, keyword, embedding.tobytes(), embedding_model),
            )

    def find_matching_keywords(self, article_id: str, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find all user keywords matching an article using embedding similarity.
        
        Args:
            article_id: Article ID to match
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of matching keywords with user info and similarity scores
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 
                    u.id as user_id,
                    u.username,
                    u.email,
                    uk.id as keyword_id,
                    uk.keyword,
                    1 - (uke.embedding <=> e.embedding) AS similarity_score
                FROM users u
                JOIN user_keywords uk ON u.id = uk.user_id
                JOIN user_keyword_embeddings uke ON uk.id = uke.keyword_id
                JOIN embeddings e ON e.article_id = %s
                WHERE (1 - (uke.embedding <=> e.embedding)) >= %s
                ORDER BY similarity_score DESC
                """,
                (article_id, similarity_threshold),
            )
            results = cur.fetchall()
            return results if results else []

    def record_article_delivery(
        self, 
        user_id: int, 
        article_id: str, 
        keyword_id: int,
        similarity_score: float
    ) -> None:
        """
        Record that an article was delivered to a user due to a matching keyword.
        
        Args:
            user_id: User ID
            article_id: Article ID
            keyword_id: Keyword ID that matched
            similarity_score: Embedding similarity score
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO user_article_delivery (user_id, article_id, keyword_id, similarity_score)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, article_id) DO UPDATE 
                SET delivered_at = CURRENT_TIMESTAMP, similarity_score = EXCLUDED.similarity_score
                """,
                (user_id, article_id, keyword_id, similarity_score),
            )

    def get_user_articles(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all articles delivered to a user, sorted by delivery date.
        
        Args:
            user_id: User ID
            limit: Maximum number of articles to return
            
        Returns:
            List of articles with delivery info
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 
                    a.id,
                    a.title,
                    a.description,
                    a.source_site,
                    a.content_url,
                    a.published_date,
                    uk.keyword,
                    uad.similarity_score,
                    uad.delivered_at
                FROM user_article_delivery uad
                JOIN articles a ON uad.article_id = a.id
                JOIN user_keywords uk ON uad.keyword_id = uk.id
                WHERE uad.user_id = %s
                ORDER BY uad.delivered_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            results = cur.fetchall()
            return results if results else []

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get statistics for a user (keywords count, articles delivered).
        
        Args:
            user_id: User ID
            
        Returns:
            Stats dictionary
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            
            # Get user info
            cur.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            
            if not user:
                return {}
            
            # Get keyword count
            cur.execute("SELECT COUNT(*) as count FROM user_keywords WHERE user_id = %s", (user_id,))
            keywords_count = cur.fetchone()["count"]
            
            # Get article delivery count
            cur.execute("SELECT COUNT(*) as count FROM user_article_delivery WHERE user_id = %s", (user_id,))
            articles_count = cur.fetchone()["count"]
            
            # Get average similarity score
            cur.execute(
                "SELECT AVG(similarity_score) as avg_score FROM user_article_delivery WHERE user_id = %s",
                (user_id,)
            )
            avg_score = cur.fetchone()["avg_score"] or 0.0
            
            return {
                "user_id": user_id,
                "username": user["username"],
                "email": user["email"],
                "keywords_count": keywords_count,
                "articles_delivered": articles_count,
                "average_similarity": round(float(avg_score), 3),
            }

