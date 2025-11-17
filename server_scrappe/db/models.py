from typing import Any, Dict, Optional, List
from datetime import datetime
from server_scrappe.db.connection import get_connection, get_cursor
import json


def _to_pg_array(py_list: Optional[List[str]]):
    """Convert Python list to PostgreSQL array literal for psycopg2 if needed.
    We can also pass Python list directly when using psycopg2 with adapters, but
    keeping this helper for explicit control.
    """
    if py_list is None:
        return None
    return py_list


def upsert_article(article: Dict[str, Any]):
    """Insert or update an article record into the `articles` table.

    Expects article to be a dict with keys matching the schema. Missing keys will be
    treated as NULL or sensible defaults.
    """
    conn = get_connection()
    cur = get_cursor(conn, dict_cursor=False)

    # Prepare fields
    title = article.get("title")
    description = article.get("description")
    summary = article.get("summary")
    tags = _to_pg_array(article.get("tags") or [])
    keywords = _to_pg_array(article.get("keywords") or [])
    full_text = article.get("full_text") or ""
    pdf_path = article.get("pdf_path")
    source = article.get("source")
    source_url = article.get("source_url")
    author = article.get("author")
    published_at = article.get("published_at")
    scraped_at = article.get("scraped_at") or datetime.utcnow()
    # normalize scraped_at if provided as ISO string
    if isinstance(scraped_at, str):
        try:
            scraped_at = datetime.fromisoformat(scraped_at)
        except Exception:
            # leave as-is; psycopg2 can accept many string datetime formats
            pass
    cluster_id = article.get("cluster_id")
    confidence_score = article.get("confidence_score")
    notified = article.get("notified", False)
    notification_sent_at = article.get("notification_sent_at")

    # Embedding handled externally; set to NULL for now (embedding_json column used if no vector)
    sql = """
    INSERT INTO articles (
        title, description, summary, tags, keywords, full_text,
        pdf_path,
        source, source_url, author, published_at, scraped_at,
        cluster_id, confidence_score, notified, notification_sent_at
    ) VALUES (
        %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s
    )
    ON CONFLICT (source, source_url) DO UPDATE SET
        title = EXCLUDED.title,
        description = EXCLUDED.description,
        summary = EXCLUDED.summary,
        tags = EXCLUDED.tags,
        keywords = EXCLUDED.keywords,
        full_text = EXCLUDED.full_text,
        pdf_path = EXCLUDED.pdf_path,
        author = EXCLUDED.author,
        published_at = EXCLUDED.published_at,
        scraped_at = EXCLUDED.scraped_at,
        cluster_id = EXCLUDED.cluster_id,
        confidence_score = EXCLUDED.confidence_score,
        notified = EXCLUDED.notified,
        notification_sent_at = EXCLUDED.notification_sent_at
    RETURNING id
    """

    params = [
        title, description, summary, tags, keywords, full_text,
        pdf_path,
        source, source_url, author, published_at, scraped_at,
        cluster_id, confidence_score, notified, notification_sent_at
    ]

    try:
        cur.execute(sql, params)
        returned = cur.fetchone()
        conn.commit()
        return returned[0] if returned else None
    except Exception as e:
        conn.rollback()
        # Surface error for debugging
        print(f"[db.models.upsert] ERROR: {e}")
        raise
    finally:
        cur.close()
        conn.close()
