#!/usr/bin/env python3
"""
Usage examples for the watch server.
"""

import asyncio
from main import WatchServer
from config import DEV_CONFIG, PROD_CONFIG


def example_backfill():
    """Example 1: Backfill mode (history)."""
    print("\n" + "="*60)
    print("EXAMPLE 1 : BACKFILL Mode")
    print("="*60)
    
    server = WatchServer(
        db_path="test_backfill.db",
        use_dummy_embeddings=True,
        check_interval=300
    )
    
    print("\n✓ Server created, launching backfill...")
    server.run_backfill_mode(limit_per_scraper=10)
    
    server.print_stats()


def example_watch_limited():
    """Example 2: Watch mode with iteration limit (for testing)."""
    print("\n" + "="*60)
    print("EXAMPLE 2 : WATCH Mode (limited to 3 iterations)")
    print("="*60)
    
    server = WatchServer(
        db_path="test_watch.db",
        use_dummy_embeddings=True,
        check_interval=10
    )
    
    print("\n✓ Server created, launching watch (3 iterations)...")
    print("  Each iteration scrapes all sources\n")
    
    try:
        import threading
        
        def stop_after_30s(srv):
            import time
            time.sleep(30)
            srv.running = False
            print("\n⏹️  Auto-stopped after 30 seconds")
        
        thread = threading.Thread(target=stop_after_30s, args=(server,), daemon=True)
        thread.start()
        
        asyncio.run(server.run_watch_mode())
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
    
    server.print_stats()


def example_multi_source_stats():
    """Example 3: View stats with multiple sources scraped."""
    print("\n" + "="*60)
    print("EXAMPLE 3 : Backfill + Stats")
    print("="*60)
    
    server = WatchServer(db_path="test_multi.db")
    
    print("\n📥 Scraping each source...")
    server.run_backfill_mode(limit_per_scraper=5)
    
    print("\n📊 Checking stats...")
    stats = server.get_stats()
    
    print(f"\nSummary :")
    print(f"  Total articles : {stats['total_articles']}")
    print(f"  Embeddings : {stats['total_embeddings']}")
    print(f"  Missing : {stats['articles_without_embeddings']}")
    
    print(f"\nPer source :")
    for source, count in sorted(stats['articles_by_source'].items()):
        pct = 100 * count / max(1, stats['total_articles'])
        print(f"  {source:15} : {count:3} ({pct:.1f}%)")


def example_custom_config():
    """Example 4: Use custom configuration."""
    print("\n" + "="*60)
    print("EXAMPLE 4 : Custom Configuration")
    print("="*60)
    
    from config import ServerConfig, ScraperConfig
    
    custom_config = ServerConfig(
        db_path="test_custom.db",
        watch_interval_seconds=120,
        use_dummy_embeddings=True,
        scrapers={
            "arxiv": ScraperConfig(enabled=True, limit_latest=10, limit_all=30),
            "github": ScraperConfig(enabled=True, limit_latest=15, limit_all=50),
            "medium": ScraperConfig(enabled=False),
            "lemonde": ScraperConfig(enabled=False),
            "huggingface": ScraperConfig(enabled=True, limit_latest=10, limit_all=30),
        }
    )
    
    print(f"\n✓ Custom config created")
    print(f"  DB : {custom_config.db_path}")
    print(f"  Interval : {custom_config.watch_interval_seconds}s")
    print(f"  Dummy embeddings : {custom_config.use_dummy_embeddings}")
    
    print(f"\n✓ Enabled scrapers :")
    for name, cfg in custom_config.scrapers.items():
        if cfg.enabled:
            print(f"  - {name} (latest:{cfg.limit_latest}, all:{cfg.limit_all})")


if __name__ == "__main__":
    import sys
    
    print("\n" + "="*60)
    print("USAGE EXAMPLES")
    print("Watch Server")
    print("="*60)
    
    examples = {
        "1": ("Backfill (history)", example_backfill),
        "2": ("Watch limited (test)", example_watch_limited),
        "3": ("Multi-source stats", example_multi_source_stats),
        "4": ("Custom config", example_custom_config),
    }
    
    print("\nChoose an example :")
    for key, (desc, _) in examples.items():
        print(f"  {key}. {desc}")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\nEnter your choice (1-4) : ").strip()
    
    if choice in examples:
        try:
            examples[choice][1]()
        except Exception as e:
            print(f"\n❌ Error : {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"❌ Invalid choice : {choice}")
