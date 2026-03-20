"""One-shot script to compute embeddings for all user keywords missing embeddings."""

import os
import logging

from database import DatabaseManager
from embeddings import EmbeddingManager, OpenAIEmbeddingProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL", "postgresql://sachahenneveux@localhost:5432/earlytech")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def main():
    provider = OpenAIEmbeddingProvider(model=EMBEDDING_MODEL)
    dim = provider.get_dimension() or 1536
    db = DatabaseManager(DB_URL, embedding_dimension=dim)
    em = EmbeddingManager(provider, expected_dimension=dim)

    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT uk.id, uk.user_id, uk.keyword
            FROM user_keywords uk
            LEFT JOIN user_keyword_embeddings uke ON uk.id = uke.keyword_id
            WHERE uke.id IS NULL
            """
        )
        keywords = cur.fetchall()

    if not keywords:
        logger.info("All keywords already have embeddings.")
        return

    logger.info(f"Found {len(keywords)} keywords without embeddings.")

    for kw in keywords:
        try:
            embedding = em.embed_text(kw["keyword"])
            db.store_keyword_embedding(
                keyword_id=str(kw["id"]),
                user_id=str(kw["user_id"]),
                keyword=kw["keyword"],
                embedding=embedding,
            )
            logger.info(f"Embedded keyword: '{kw['keyword']}'")
        except Exception as e:
            logger.error(f"Failed to embed '{kw['keyword']}': {e}")

    # Now dispatch all articles to users
    logger.info("Dispatching articles to users...")
    from keyword_matcher import KeywordMatcher

    matcher = KeywordMatcher(db_manager=db, embedding_manager=em, similarity_threshold=0.25)

    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM articles")
        article_ids = [row["id"] for row in cur.fetchall()]

    total_deliveries = 0
    for article_id in article_ids:
        try:
            result = matcher.dispatch_article_to_users(article_id)
            if result:
                total_deliveries += len(result)
        except Exception as e:
            logger.error(f"Dispatch error for {article_id}: {e}")

    logger.info(f"Done. {total_deliveries} deliveries recorded.")


if __name__ == "__main__":
    main()
