"""
Examples - User Keywords Filtering System

This demonstrates how to use the keyword filtering system:
1. Create users
2. Add keywords
3. Process articles
4. Retrieve personalized feeds
"""

import os
import sys
from typing import List

from database import DatabaseManager
from embeddings import EmbeddingManager, OpenAIEmbeddingProvider
from keyword_matcher import KeywordMatcher


def setup_example_users():
    """Create example users with keywords."""
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/veille_technique")
    
    db_manager = DatabaseManager(db_url)
    embedding_provider = OpenAIEmbeddingProvider()
    embedding_manager = EmbeddingManager(embedding_provider)
    keyword_matcher = KeywordMatcher(db_manager, embedding_manager)
    
    print("\n" + "="*60)
    print("SETUP EXAMPLE USERS")
    print("="*60)
    
    print("\nCreating User 1: Marie (AI/ML Engineer)")
    user1_id = db_manager.add_user(username="marie", email="marie@tech.com")
    print(f" User ID: {user1_id}")
    
    user1_keywords = [
        "machine learning",
        "deep learning",
        "neural networks",
        "transformers",
        "GPT",
        "BERT",
        "computer vision",
        "natural language processing"
    ]
    
    keyword_map = keyword_matcher.setup_user_keywords(user1_id, user1_keywords)
    print(f" Added {len(keyword_map)} keywords")
    
    print("\nCreating User 2: Lucas (DevOps Engineer)")
    user2_id = db_manager.add_user(username="lucas", email="lucas@ops.com")
    print(f" User ID: {user2_id}")
    
    user2_keywords = [
        "Kubernetes",
        "Docker",
        "CI/CD",
        "GitHub Actions",
        "deployment",
        "infrastructure",
        "cloud computing",
        "AWS"
    ]
    
    keyword_map = keyword_matcher.setup_user_keywords(user2_id, user2_keywords)
    print(f"  ✓ Added {len(keyword_map)} keywords")
    
    print("\nCreating User 3: Sophie (Web Developer)")
    user3_id = db_manager.add_user(username="sophie", email="sophie@web.com")
    print(f"User ID: {user3_id}")
    
    user3_keywords = [
        "React",
        "Vue.js",
        "JavaScript",
        "TypeScript",
        "frontend",
        "web development",
        "HTML",
        "CSS"
    ]
    
    keyword_map = keyword_matcher.setup_user_keywords(user3_id, user3_keywords)
    print(f"Added {len(keyword_map)} keywords")
    
    print("\n" + "="*60)
    print(f"Setup complete! 3 users created with keywords")
    print("="*60)
    
    return {
        "user1": {"id": user1_id, "name": "Marie"},
        "user2": {"id": user2_id, "name": "Lucas"},
        "user3": {"id": user3_id, "name": "Sophie"},
    }


def test_article_matching(article_id: str, similarity_threshold: float = 0.7):
    """Test matching an article with user keywords."""
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/veille_technique")
    
    db_manager = DatabaseManager(db_url)
    embedding_provider = OpenAIEmbeddingProvider()
    embedding_manager = EmbeddingManager(embedding_provider)
    keyword_matcher = KeywordMatcher(db_manager, embedding_manager, similarity_threshold)
    
    print(f"\nTesting article matching for {article_id}...")
    
    keyword_matcher.print_matching_summary(article_id)
    
    print("\nDispatching article to users...")
    delivery_summary = keyword_matcher.dispatch_article_to_users(article_id)
    
    if delivery_summary:
        print(f"\nArticle delivered to {len(delivery_summary)} users:")
        for user_id, keywords in delivery_summary.items():
            print(f"   - User {user_id}: via keywords {keywords}")
    else:
        print("\nNo users matched for this article")


def get_user_feed(user_id: int, limit: int = 10):
    """Get personalized feed for a user."""
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/veille_technique")
    
    db_manager = DatabaseManager(db_url)
    embedding_provider = OpenAIEmbeddingProvider()
    embedding_manager = EmbeddingManager(embedding_provider)
    keyword_matcher = KeywordMatcher(db_manager, embedding_manager)
    
    print(f"\nFetching personalized feed for user {user_id}...")
    
    feed = keyword_matcher.get_user_personalized_feed(user_id, limit=limit)
    
    if not feed:
        print("No articles in feed yet")
        return
    
    print(f"\nFound {len(feed)} articles:")
    print("="*60)
    
    for i, article in enumerate(feed, 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Source: {article['source_site']}")
        print(f"   Keyword: {article['keyword']}")
        print(f"   Similarity: {article['similarity_score']*100:.1f}%")
        print(f"   Delivered: {article['delivered_at']}")
        print(f"   URL: {article['content_url']}")


def print_user_stats(user_id: int):
    """Print statistics for a user."""
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/veille_technique")
    
    db_manager = DatabaseManager(db_url)
    
    stats = db_manager.get_user_stats(user_id)
    
    if not stats:
        print(f"User {user_id} not found")
        return
    
    print("\n" + "="*60)
    print(f"User Statistics: {stats['username']}")
    print("="*60)
    print(f"Email: {stats['email']}")
    print(f"Keywords: {stats['keywords_count']}")
    print(f"Articles Delivered: {stats['articles_delivered']}")
    print(f"Average Match Score: {stats['average_similarity']*100:.1f}%")
    print("="*60)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            setup_example_users()
        
        elif command == "feed" and len(sys.argv) > 2:
            user_id = int(sys.argv[2])
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            get_user_feed(user_id, limit=limit)
        
        elif command == "stats" and len(sys.argv) > 2:
            user_id = int(sys.argv[2])
            print_user_stats(user_id)
        
        elif command == "match" and len(sys.argv) > 2:
            article_id = sys.argv[2]
            threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.7
            test_article_matching(article_id, threshold)
        
        else:
            print("Usage:")
            print("  python examples_user_keywords.py setup              - Create example users")
            print("  python examples_user_keywords.py feed <user_id> [limit]  - Get user feed")
            print("  python examples_user_keywords.py stats <user_id>     - Get user stats")
            print("  python examples_user_keywords.py match <article_id> [threshold] - Test matching")
    else:
        print("""
    User Keywords Filtering System - Examples

Usage:
  python examples_user_keywords.py setup                    - Create example users
  python examples_user_keywords.py feed <user_id> [limit]  - Get user personalized feed
  python examples_user_keywords.py stats <user_id>          - Show user statistics
  python examples_user_keywords.py match <article_id> [threshold] - Test article matching

Environment:
  Set DATABASE_URL to change the PostgreSQL connection

Example Flow:
  1. python examples_user_keywords.py setup                 # Create users with keywords
  2. python main.py watch                                   # Scrape and dispatch articles
  3. python examples_user_keywords.py feed 1               # View personalized feed for user 1
        """)
