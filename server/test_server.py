"""
Quick server tests - Verify all components are functional.
"""

import sys
import os

def test_imports():
    """Test that all imports work."""
    print("🧪 Test 1 : Checking imports...")
    try:
        from database import DatabaseManager
        from embeddings import EmbeddingManager, DummyEmbeddingProvider
        from config import ServerConfig
        print("  ✓ Core imports OK")
        
        from scrapers.base import BaseScraper
        print("  ✓ BaseScraper OK")
        
        try:
            from scrapers.arxiv_scraper import ArxivScraper
            print("  ✓ ArxivScraper OK")
        except ImportError as e:
            print(f"  ⚠️  ArxivScraper : {e}")
        
        from scrapers.github_scraper import GithubScraper
        print("  ✓ GithubScraper OK")
        
        from scrapers.medium_scraper import MediumScraper
        print("  ✓ MediumScraper OK")
        
        from scrapers.lemonde_scraper import LeMondeScraper
        print("  ✓ LeMondeScraper OK")
        
        from scrapers.huggingface_scraper import HuggingFaceScraper
        print("  ✓ HuggingFaceScraper OK")
        
        return True
    except Exception as e:
        print(f"  ❌ Error : {e}")
        return False


def test_database():
    """Test that database works."""
    print("\n🧪 Test 2 : Checking database...")
    try:
        from database import DatabaseManager
        
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        
        try:
            db = DatabaseManager(db_path)
            print("  ✓ DB created")
            
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cur.fetchall()]
                
                expected = {"articles", "embeddings", "sync_history"}
                if expected.issubset(set(tables)):
                    print(f"  ✓ Tables created : {', '.join(sorted(tables))}")
                else:
                    print(f"  ❌ Missing tables. Found : {tables}")
                    return False
            
            test_article = {
                "id": "test-123",
                "source_site": "test",
                "title": "Test Article",
                "description": "Test",
                "author_info": "Tester",
                "keywords": "test",
                "content_url": "http://test.com",
                "published_date": "2024-01-01T00:00:00Z",
                "item_type": "article"
            }
            
            if db.save_article(test_article):
                print("  ✓ Article inserted successfully")
            else:
                print("  ❌ Error during insertion")
                return False
            
            if db.article_exists("test-123"):
                print("  ✓ Existence check OK")
            else:
                print("  ❌ Article not found after insertion")
                return False
            
            return True
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
                
    except Exception as e:
        print(f"  ❌ Error : {e}")
        import traceback
        traceback.print_exc()
        return False


def test_embeddings():
    """Test that embeddings work."""
    print("\n🧪 Test 3 : Checking embeddings...")
    try:
        from embeddings import EmbeddingManager, DummyEmbeddingProvider
        
        provider = DummyEmbeddingProvider(dimension=384)
        manager = EmbeddingManager(provider)
        print("  ✓ EmbeddingManager created")
        
        embedding = manager.embed_text("Test text")
        print(f"  ✓ Embedding generated ({len(embedding)} bytes)")
        
        test_article = {
            "title": "Test Title",
            "description": "Test Description"
        }
        embedding = manager.embed_article(test_article)
        print(f"  ✓ Article embedded ({len(embedding)} bytes)")
        
        import pickle
        deserialized = pickle.loads(embedding)
        print(f"  ✓ Embedding deserialized (shape: {deserialized.shape})")
        
        return True
    except Exception as e:
        print(f"  ❌ Error : {e}")
        import traceback
        traceback.print_exc()
        return False


def test_server_creation():
    """Test that server is created correctly."""
    print("\n🧪 Test 4 : Checking server creation...")
    try:
        from main import WatchServer
        
        server = WatchServer(check_interval=300)
        print("  ✓ Server created")
        
        if server.scrapers:
            print(f"  ✓ {len(server.scrapers)} scraper(s) initialized")
            for name, scraper in server.scrapers.items():
                print(f"    - {name}")
        else:
            print("  ❌ No scrapers initialized")
            return False
        
        if server.db_manager and server.embedding_manager:
            print("  ✓ DatabaseManager and EmbeddingManager OK")
        else:
            print("  ❌ Managers not initialized")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ Error : {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🧪 QUICK TESTS - Watch Server")
    print("="*60)
    
    tests = [
        test_imports,
        test_database,
        test_embeddings,
        test_server_creation,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\n❌ Unhandled exception in {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print(f"\nTotal : {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
