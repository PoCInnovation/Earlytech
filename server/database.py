"""Database manager for the server."""

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime, UTC
from contextlib import contextmanager
import os


class DatabaseManager:
    """Manages unified database operations."""
    
    def __init__(self, db_path: str = "technical_watch.db"):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite file
        """
        self.db_path = db_path
        self.setup_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def setup_database(self):
        """Initialize database and create tables."""
        with self.get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cur = conn.cursor()
            
            cur.execute("""
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
                published_date TEXT,
                item_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            cur.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL UNIQUE,
                embedding BLOB NOT NULL,
                embedding_model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
            """)
            
            cur.execute("""
            CREATE TABLE IF NOT EXISTS sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_site TEXT NOT NULL,
                sync_mode TEXT NOT NULL,
                last_sync_time TIMESTAMP,
                items_processed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            cur.execute("CREATE INDEX IF NOT EXISTS idx_content_hash ON articles(content_hash)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_source_site ON articles(source_site)")
            
            conn.commit()
    
    def save_article(self, item: Dict, conn: Optional[sqlite3.Connection] = None) -> bool:
        """
        Save article to database.
        
        Args:
            item: Dict with unified structure
            conn: Optional connection (for transactions)
            
        Returns:
            True if inserted, False if already exists
        """
        import hashlib
        
        should_close = False
        if conn is None:
            conn = sqlite3.connect(self.db_path)
            should_close = True
        
        try:
            cur = conn.cursor()
            
            full_content = item.get("full_content", item.get("description", ""))
            content_hash = hashlib.sha256(full_content.encode()).hexdigest()
            
            cur.execute("""
            INSERT OR IGNORE INTO articles
            (id, source_site, title, description, full_content, content_hash, author_info, keywords, content_url, published_date, item_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item["id"],
                item["source_site"],
                item["title"],
                item.get("description", ""),
                full_content,
                content_hash,
                item.get("author_info", ""),
                item.get("keywords", ""),
                item["content_url"],
                item.get("published_date", datetime.now(UTC).isoformat()),
                item.get("item_type", "article"),
                datetime.now(UTC).isoformat()
            ))
            
            conn.commit()
            return cur.rowcount > 0
            
        finally:
            if should_close:
                conn.close()
    
    def save_articles_batch(self, items: List[Dict]) -> int:
        """
        Save multiple articles in one transaction.
        
        Args:
            items: List of dicts with unified structure
            
        Returns:
            Number of articles inserted
        """
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
            cur.execute("SELECT 1 FROM articles WHERE id = ?", (article_id,))
            return cur.fetchone() is not None
    
    def article_exists_by_hash(self, content_hash: str) -> bool:
        """
        Check if article already exists by content hash.
        
        Args:
            content_hash: SHA256 hash of article content
            
        Returns:
            True if article with same content exists
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM articles WHERE content_hash = ?", (content_hash,))
            return cur.fetchone() is not None
    
    def get_article_by_hash(self, content_hash: str) -> Optional[Dict]:
        """
        Get article by content hash.
        
        Args:
            content_hash: SHA256 hash of article content
            
        Returns:
            Article dict if found, None otherwise
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM articles WHERE content_hash = ?", (content_hash,))
            row = cur.fetchone()
            return dict(row) if row else None
    
    def save_embedding(self, article_id: str, embedding: bytes, model: str = "default") -> bool:
        """
        Save article embedding.
        
        Args:
            article_id: Article ID
            embedding: Embedding in bytes format
            model: Name of the model used
            
        Returns:
            True if saved, False otherwise
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            
            try:
                cur.execute("""
                INSERT OR IGNORE INTO embeddings
                (article_id, embedding, embedding_model)
                VALUES (?, ?, ?)
                """, (article_id, embedding, model))
                
                conn.commit()
                return cur.rowcount > 0
                
            except sqlite3.IntegrityError:
                return False
    
    def get_articles_without_embeddings(self, limit: int = 100) -> List[Dict]:
        """
        Get articles without embeddings.
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List of articles
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("""
            SELECT a.* FROM articles a
            LEFT JOIN embeddings e ON a.id = e.article_id
            WHERE e.id IS NULL
            LIMIT ?
            """, (limit,))
            
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    
    def get_articles_by_source(self, source: str, limit: int = 50) -> List[Dict]:
        """Get articles from a specific source."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("""
            SELECT * FROM articles
            WHERE source_site = ?
            ORDER BY published_date DESC
            LIMIT ?
            """, (source, limit))
            
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    
    def get_total_articles(self) -> int:
        """Return total number of articles."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM articles")
            return cur.fetchone()[0]
    
    def get_articles_by_source_count(self) -> Dict[str, int]:
        """Return number of articles per source."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT source_site, COUNT(*) as count
            FROM articles
            GROUP BY source_site
            ORDER BY count DESC
            """)
            
            return {row[0]: row[1] for row in cur.fetchall()}
    
    def record_sync(self, source: str, mode: str, items_processed: int = 0):
        """
        Record a synchronization.
        
        Args:
            source: Source name
            mode: "watch" or "backfill"
            items_processed: Number of items processed
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("""
            INSERT INTO sync_history
            (source_site, sync_mode, last_sync_time, items_processed)
            VALUES (?, ?, ?, ?)
            """, (source, mode, datetime.now(UTC).isoformat(), items_processed))
            
            conn.commit()
    
    def get_last_sync(self, source: str, mode: str) -> Optional[Dict]:
        """Get last sync for a source and mode."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("""
            SELECT * FROM sync_history
            WHERE source_site = ? AND sync_mode = ?
            ORDER BY created_at DESC
            LIMIT 1
            """, (source, mode))
            
            row = cur.fetchone()
            return dict(row) if row else None
    
    def get_stats(self) -> Dict:
        """Return database statistics."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("SELECT COUNT(*) FROM articles")
            total_articles = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM embeddings")
            total_embeddings = cur.fetchone()[0]
            
            cur.execute("""
            SELECT source_site, COUNT(*) as count
            FROM articles
            GROUP BY source_site
            """)
            
            articles_by_source = {row[0]: row[1] for row in cur.fetchall()}
            
            return {
                "total_articles": total_articles,
                "total_embeddings": total_embeddings,
                "articles_by_source": articles_by_source,
                "articles_without_embeddings": total_articles - total_embeddings
            }
