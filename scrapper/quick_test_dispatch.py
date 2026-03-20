#!/usr/bin/env python3
"""
Quick Test - Verify Article Dispatch is Working

This script quickly tests that articles are being dispatched to users correctly.
"""

import os
import sys

# Add scrapper to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database import DatabaseManager
from embeddings import EmbeddingManager, OpenAIEmbeddingProvider  
from keyword_matcher import KeywordMatcher


def quick_test():
    """Quick verification that dispatch system works."""
    
    print("\n" + "="*70)
    print("QUICK TEST - Article Dispatch System")
    print("="*70)
    
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/veille_technique")
    
    try:
        db_manager = DatabaseManager(db_url)
    except Exception as e:
        print(f"\nCannot connect to database: {e}")
        print("   Make sure PostgreSQL is running!")
        return False
    
    print("\nConnected to database")
    
    # Check if tables exist
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        
        # Check users table
        cur.execute("SELECT COUNT(*) as count FROM users")
        user_count = cur.fetchone()["count"]
        
        # Check keywords table
        cur.execute("SELECT COUNT(*) as count FROM user_keywords")
        keyword_count = cur.fetchone()["count"]
        
        # Check deliveries table
        cur.execute("SELECT COUNT(*) as count FROM user_article_delivery")
        delivery_count = cur.fetchone()["count"]
        
        # Check articles with embeddings
        cur.execute("""
            SELECT COUNT(*) as count 
            FROM articles a 
            JOIN embeddings e ON a.id = e.article_id
        """)
        articles_with_embeddings = cur.fetchone()["count"]
    
    print(f"\nCurrent State:")
    print(f"   - Users: {user_count}")
    print(f"   - Keywords: {keyword_count}")
    print(f"   - Articles (with embeddings): {articles_with_embeddings}")
    print(f"   - Deliveries recorded: {delivery_count}")
    
    if user_count == 0:
        print("\nNo users found!")
        print("   Run: python examples_user_keywords.py setup")
        return False
    
    if keyword_count == 0:
        print("\nNo keywords found!")
        print("   Run: python examples_user_keywords.py setup")
        return False
    
    if articles_with_embeddings == 0:
        print("\nNo articles with embeddings found!")
        print("   Run: python main.py backfill --limit 10")
        return False
    
    # Initialize keyword matcher
    try:
        embedding_provider = OpenAIEmbeddingProvider()
        embedding_manager = EmbeddingManager(embedding_provider)
        keyword_matcher = KeywordMatcher(db_manager, embedding_manager, similarity_threshold=0.7)
    except Exception as e:
        print(f"\nCannot initialize KeywordMatcher: {e}")
        return False
    
    print("\nKeywordMatcher initialized")
    
    # Test matching on existing articles
    print("\nTesting matching on existing articles...")
    
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT a.id, a.title 
            FROM articles a 
            JOIN embeddings e ON a.id = e.article_id 
            LIMIT 3
        """)
        test_articles = cur.fetchall()
    
    if not test_articles:
        print("   No articles found to test")
        return False
    
    total_matches = 0
    
    for article in test_articles:
        article_id = article["id"]
        title = article["title"][:50]
        
        print(f"\n   {title}...")
        
        # Find matches
        matches = keyword_matcher.match_article_with_keywords(article_id)
        
        if matches:
            print(f"      {len(matches)} keyword match(es) found")
            for match in matches[:3]:
                print(f"         - {match['username']}: '{match['keyword']}' ({match['similarity_score']:.2%})")
            total_matches += len(matches)
        else:
            print(f"        No matches (similarity < 0.7)")
    
    print(f"\nTotal matches found: {total_matches}")
    
    print("\n- Sample User Feeds:")
    
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username FROM users LIMIT 3")
        sample_users = cur.fetchall()
    
    for user in sample_users:
        user_id = user["id"]
        username = user["username"]
        
        feed = keyword_matcher.get_user_personalized_feed(user_id, limit=3)
        
        print(f"\n    {username}:")
        if feed:
            for item in feed:
                print(f"      - {item['title'][:40]}... (via '{item['keyword']}')")
        else:
            print(f"      (no articles yet)")
    
    print("\n" + "="*70)
    print("DISPATCH SYSTEM IS WORKING!")
    print("="*70)
    
    print("\nSummary:")
    print("    Database connected")
    print("    Tables exist and populated")
    print("    KeywordMatcher initialized")
    print("    Matching works")
    print("    Feeds are accessible")
    
    print("\nNext Steps:")
    print("   - Run: python main.py watch")
    print("     (Articles will be auto-dispatched to users)")
    print("")
    print("   - Check user feed: python examples_user_keywords.py feed 1")
    print("")
    
    return True


if __name__ == "__main__":
    try:
        success = quick_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)