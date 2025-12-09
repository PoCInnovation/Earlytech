"""
Watch Server - Technical surveillance with watch and backfill modes.

Modes:
1. "watch": Scrape new articles continuously
2. "backfill": Retrieve entire available history at startup
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, UTC
import argparse

from database import DatabaseManager
from embeddings import EmbeddingManager, DummyEmbeddingProvider
from scrapers.arxiv_scraper import ArxivScraper
from scrapers.github_scraper import GithubScraper
from scrapers.medium_scraper import MediumScraper
from scrapers.lemonde_scraper import LeMondeScraper
from scrapers.huggingface_scraper import HuggingFaceScraper


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WatchServer:
    """Technical watch server with watch and backfill modes."""
    
    def __init__(
        self,
        db_path: str = "veille_technique.db",
        use_dummy_embeddings: bool = True,
        check_interval: int = 300
    ):
        """
        Initialize the server.
        
        Args:
            db_path: Path to the database file
            use_dummy_embeddings: Use dummy embeddings (dev) or real ones
            check_interval: Scraping interval in seconds (watch mode)
        """
        self.db_manager = DatabaseManager(db_path)
        
        if use_dummy_embeddings:
            embedding_provider = DummyEmbeddingProvider()
        else:
            embedding_provider = DummyEmbeddingProvider()
        
        self.embedding_manager = EmbeddingManager(embedding_provider)
        
        self.check_interval = check_interval
        self.running = False
        
        self.scrapers = self._init_scrapers()
    
    def _init_scrapers(self) -> Dict[str, object]:
        """Initialize all available scrapers."""
        scrapers = {}
        
        try:
            scrapers["arxiv"] = ArxivScraper(category="cs.LG")
            logger.info("✓ ArXiv scraper initialized")
        except ImportError as e:
            logger.warning(f"✗ ArXiv scraper failed: {e}")
        
        try:
            scrapers["github"] = GithubScraper()
            logger.info("✓ GitHub scraper initialized")
        except Exception as e:
            logger.warning(f"✗ GitHub scraper failed: {e}")
        
        try:
            scrapers["medium"] = MediumScraper()
            logger.info("✓ Medium scraper initialized")
        except ImportError as e:
            logger.warning(f"✗ Medium scraper failed: {e}")
        
        try:
            scrapers["lemonde"] = LeMondeScraper()
            logger.info("✓ Le Monde scraper initialized")
        except ImportError as e:
            logger.warning(f"✗ Le Monde scraper failed: {e}")
        
        try:
            scrapers["huggingface"] = HuggingFaceScraper()
            logger.info("✓ Hugging Face scraper initialized")
        except Exception as e:
            logger.warning(f"✗ Hugging Face scraper failed: {e}")
        
        return scrapers
    
    def _process_articles(self, articles: List[Dict]) -> int:
        """
        Process articles: save to DB and create embeddings.
        
        Args:
            articles: List of normalized articles
            
        Returns:
            Number of new articles processed
        """
        import hashlib
        
        new_count = 0
        
        for article in articles:
            if self.db_manager.article_exists(article["id"]):
                continue
            
            full_content = article.get("full_content", article.get("description", ""))
            content_hash = hashlib.sha256(full_content.encode()).hexdigest()
            
            if self.db_manager.article_exists_by_hash(content_hash):
                logger.debug(f"Article {article['id']} is duplicate (same content hash)")
                continue
            
            if self.db_manager.save_article(article):
                new_count += 1
                
                try:
                    embedding = self.embedding_manager.embed_article(article)
                    self.db_manager.save_embedding(
                        article["id"],
                        embedding,
                        model=self.embedding_manager.get_provider_name()
                    )
                except Exception as e:
                    logger.error(f"Embedding error for {article['id']}: {e}")
        
        return new_count
    
    def run_backfill_mode(self, limit_per_scraper: int = 100):
        """
        Launch backfill mode - scrape entire available history.
        
        Args:
            limit_per_scraper: Maximum articles per scraper
        """
        logger.info("=" * 60)
        logger.info("🔄 BACKFILL MODE START (History)")
        logger.info("=" * 60)
        
        total_new = 0
        
        for source_name, scraper in self.scrapers.items():
            logger.info(f"\n📥 Scraping {source_name} (backfill mode)...")
            
            try:
                articles = scraper.scrape_all(limit=limit_per_scraper)
                
                if not articles:
                    logger.info(f"  ⚠️  No articles found for {source_name}")
                    continue
                
                logger.info(f"  📦 {len(articles)} articles received")
                
                new_count = self._process_articles(articles)
                total_new += new_count
                
                logger.info(f"  ✓ {new_count} new articles saved")
                
                self.db_manager.record_sync(source_name, "backfill", new_count)
                
            except Exception as e:
                logger.error(f"  ✗ Error for {source_name}: {e}")
        
        logger.info("\n" + "=" * 60)
        logger.info(f"✓ BACKFILL MODE COMPLETE - {total_new} articles processed")
        logger.info("=" * 60)
    
    async def run_watch_mode(self):
        """Launch watch mode - scrape continuously."""
        logger.info("=" * 60)
        logger.info("👀 WATCH MODE START (Surveillance)")
        logger.info(f"Scraping interval: {self.check_interval}s")
        logger.info("=" * 60)
        
        self.running = True
        iteration = 0
        
        try:
            while self.running:
                iteration += 1
                logger.info(f"\n[Iteration {iteration}] {datetime.now(UTC).isoformat()}")
                
                total_new = 0
                
                for source_name, scraper in self.scrapers.items():
                    logger.info(f"  📡 Scraping {source_name}...")
                    
                    try:
                        articles = scraper.scrape_latest(limit=20)
                        
                        if not articles:
                            logger.info(f"    - No new articles")
                            continue
                        
                        new_count = self._process_articles(articles)
                        total_new += new_count
                        
                        if new_count > 0:
                            logger.info(f"    ✓ {new_count} new articles")
                            self.db_manager.record_sync(source_name, "watch", new_count)
                        else:
                            logger.info(f"    - All articles already exist")
                        
                    except Exception as e:
                        logger.error(f"    ✗ Error: {e}")
                
                logger.info(f"  📊 Total: {total_new} new articles")
                logger.info(f"  ⏳ Waiting {self.check_interval}s...")
                
                stats = self.db_manager.get_stats()
                logger.info(f"  📈 DB: {stats['total_articles']} articles, "
                           f"{stats['articles_without_embeddings']} without embedding")
                
                await asyncio.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("\n⏹️  Server stopped")
        finally:
            self.running = False
    
    def get_stats(self) -> Dict:
        """Return database statistics."""
        return self.db_manager.get_stats()
    
    def print_stats(self):
        """Display database statistics."""
        stats = self.get_stats()
        
        print("\n" + "=" * 60)
        print("📊 DATABASE STATISTICS")
        print("=" * 60)
        print(f"Total articles: {stats['total_articles']}")
        print(f"Articles with embedding: {stats['total_embeddings']}")
        print(f"Articles without embedding: {stats['articles_without_embeddings']}")
        print("\nArticles per source:")
        for source, count in stats['articles_by_source'].items():
            print(f"  - {source}: {count}")
        print("=" * 60)
    
    def export_database(self, output_path: str) -> bool:
        """
        Export database to a new file.
        
        Args:
            output_path: Path where to export the database
            
        Returns:
            True if successful, False otherwise
        """
        import shutil
        
        try:
            shutil.copy2(self.db_manager.db_path, output_path)
            logger.info(f"✓ Database exported to {output_path}")
            
            import os
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"  File size: {size_mb:.2f} MB")
            
            return True
        except Exception as e:
            logger.error(f"✗ Export failed: {e}")
            return False


def main():
    """Server entry point."""
    parser = argparse.ArgumentParser(
        description="Technical watch server with watch and backfill modes"
    )
    parser.add_argument(
        "mode",
        choices=["watch", "backfill", "stats", "export"],
        help="Execution mode"
    )
    parser.add_argument(
        "--db",
        default="veille_technique.db",
        help="Path to database"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Scraping interval in seconds (watch mode)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max articles per source (backfill mode)"
    )
    parser.add_argument(
        "--output",
        default="veille_export.db",
        help="Output file path for export mode"
    )
    parser.add_argument(
        "--no-dummy",
        action="store_true",
        help="Do not use dummy embeddings"
    )
    
    args = parser.parse_args()
    
    server = WatchServer(
        db_path=args.db,
        use_dummy_embeddings=not args.no_dummy,
        check_interval=args.interval
    )
    
    if args.mode == "backfill":
        server.run_backfill_mode(limit_per_scraper=args.limit)
        server.print_stats()
        
    elif args.mode == "watch":
        asyncio.run(server.run_watch_mode())
        
    elif args.mode == "stats":
        server.print_stats()
    
    elif args.mode == "export":
        logger.info(f"Exporting database from {args.db} to {args.output}...")
        if server.export_database(args.output):
            server.print_stats()
            logger.info(f"✓ You can now open {args.output} with SQLite Browser or your preferred tool")
        else:
            logger.error("Export failed")


if __name__ == "__main__":
    main()
