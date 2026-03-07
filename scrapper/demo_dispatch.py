"""
DEMO - Article Dispatch System
Demonstrates the complete workflow of dispatching articles to users based on keyword matching
"""

import os
import sys
import numpy as np
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from embeddings import EmbeddingManager, OpenAIEmbeddingProvider
from keyword_matcher import KeywordMatcher


def create_demo_embedding(text: str, dimension: int = 1536) -> np.ndarray:
    """Create a deterministic embedding for demo purposes."""
    np.random.seed(hash(text) % (2**32))
    emb = np.random.randn(dimension)
    return emb / np.linalg.norm(emb)


def demo_workflow():
    """
    Complete workflow demonstration:
    1. Setup users with keywords
    2. Create article with embedding
    3. Match article with keywords
    4. Dispatch to users
    5. Verify delivery
    """
    
    print("\n" + "="*80)
    print("🚀 DEMONSTRATION - Article Dispatch System")
    print("="*80)
    
    # Database connection
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/veille_technique")
    
    try:
        db_manager = DatabaseManager(db_url)
        print("Connected to database")
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("\nMake sure PostgreSQL is running and DATABASE_URL is correct")
        return
    
    try:
        embedding_provider = OpenAIEmbeddingProvider()
        print("Using OpenAI embeddings")
        use_real_embeddings = True
    except Exception as e:
        print(f" /!\ OpenAI not available ({e}), using dummy embeddings for demo")
        use_real_embeddings = False
    
    keyword_matcher = KeywordMatcher(
        db_manager=db_manager,
        embedding_manager=None if not use_real_embeddings else EmbeddingManager(embedding_provider),
        similarity_threshold=0.7
    )
    
    print("\n" + "-"*80)
    print("STEP 1: Create demo users with keywords")
    print("-"*80)
    
    # Create users
    users = [
        {
            "username": "alice_ml",
            "email": "alice@ml.com",
            "keywords": ["machine learning", "deep learning", "neural networks", "transformers"]
        },
        {
            "username": "bob_web",
            "email": "bob@web.com", 
            "keywords": ["React", "JavaScript", "TypeScript", "frontend"]
        },
        {
            "username": "charlie_ai",
            "email": "charlie@ai.com",
            "keywords": ["artificial intelligence", "GPT", "language models", "NLP"]
        }
    ]
    
    user_ids = {}
    
    for user_data in users:
        user_id = db_manager.add_user(user_data["username"], user_data["email"])
        user_ids[user_data["username"]] = user_id
        print(f"\nCreated user: {user_data['username']} (ID: {user_id})")
        for keyword in user_data["keywords"]:
            kw_id = db_manager.add_user_keyword(user_id, keyword)
            
            if use_real_embeddings:
                embedding = keyword_matcher.embedding_manager.embed_text(keyword)
            else:
                embedding = create_demo_embedding(keyword)
            db_manager.store_keyword_embedding(kw_id, user_id, keyword, embedding)
            print(f"   ✓ Keyword: '{keyword}' (similarity threshold: 0.7)")
    
    print(f"\nCreated {len(users)} users with {sum(len(u['keywords']) for u in users)} keywords total")
    
    print("\n" + "-"*80)
    print("STEP 2: Create test articles")
    print("-"*80)
    
    test_articles = [
        {
            "id": "demo_article_001",
            "title": "Advances in Transformer Models for Natural Language Processing",
            "description": "This paper presents new techniques for training large transformer models on natural language tasks, improving performance on GPT-like architectures.",
            "should_match": ["alice_ml", "charlie_ai"]  # matches
        },
        {
            "id": "demo_article_002",
            "title": "Building Modern React Applications with TypeScript",
            "description": "A comprehensive guide to building scalable React applications using TypeScript, covering hooks, state management, and best practices.",
            "should_match": ["bob_web"]  #  match
        },
        {
            "id": "demo_article_003",
            "title": "Cooking Italian Pasta: A Complete Guide",
            "description": "Learn how to cook authentic Italian pasta with traditional recipes and techniques from Italy.",
            "should_match": []  # NOT match
        }
    ]
    
    for article in test_articles:
        article_data = {
            "id": article["id"],
            "source_site": "demo",
            "title": article["title"],
            "description": article["description"],
            "full_content": article["description"],
            "content_hash": f"hash_{article['id']}",
            "author_info": "Demo Author",
            "keywords": "",
            "content_url": f"https://demo.com/{article['id']}",
            "published_date": datetime.now(UTC),
            "item_type": "article"
        }
        
        success = db_manager.save_article(article_data)
        
        if success:
            print(f"\nArticle: {article['title'][:60]}...")
            full_text = f"{article['title']} {article['description']}"
            if use_real_embeddings:
                embedding = keyword_matcher.embedding_manager.embed_text(full_text)
            else:
                embedding = create_demo_embedding(full_text)
            db_manager.save_embedding(article["id"], embedding, model="demo")
            print(f"Embedding created and saved")
        else:
            print(f"\n/!\ Article {article['id']} already exists, skipping...")
    
    print("\n" + "-"*80)
    print("🔍 STEP 3: Match articles with keywords and dispatch")
    print("-"*80)
    
    results = {}
    
    for article in test_articles:
        print(f"\nProcessing: {article['title'][:60]}...")
        
        matches = keyword_matcher.match_article_with_keywords(article["id"])
        
        if matches:
            print(f"   ✓ Found {len(matches)} keyword matches:")
            for match in matches:
                print(f"      • User {match['username']}: '{match['keyword']}' (similarity: {match['similarity_score']:.2%})")
        else:
            print(f"   /!\  No matches found (similarity < 0.7)")
        
        print(f"\nDispatching article to matching users...")
        delivery_summary = keyword_matcher.dispatch_article_to_users(article["id"])
        
        results[article["id"]] = {
            "matches": len(matches),
            "users_delivered": len(delivery_summary),
            "expected": article["should_match"]
        }
        
        if delivery_summary:
            print(f"Article delivered to {len(delivery_summary)} user(s):")
            for user_id, keywords in delivery_summary.items():
                # Find username
                username = next((k for k, v in user_ids.items() if v == user_id), f"User#{user_id}")
                print(f"      ✉️  {username} (via keywords: {keywords})")
        else:
            print(f"Article not delivered (no matches above threshold)")
    
    print("\n" + "-"*80)
    print("STEP 4: Verify user feeds")
    print("-"*80)
    
    for username, user_id in user_ids.items():
        print(f"\n {username}'s personalized feed:")
        
        feed = keyword_matcher.get_user_personalized_feed(user_id, limit=10)
        
        if feed:
            for i, item in enumerate(feed, 1):
                print(f"   {i}. {item['title'][:50]}...")
                print(f"      Matched via: '{item['keyword']}' (similarity: {item['similarity_score']:.2%})")
        else:
            print(f"   (empty - no articles matched this user's keywords)")
    
    print("\n" + "-"*80)
    print("STEP 5: User statistics")
    print("-"*80)
    
    for username, user_id in user_ids.items():
        stats = db_manager.get_user_stats(user_id)
        
        print(f"\n {stats['username']}:")
        print(f"   • Keywords: {stats['keywords_count']}")
        print(f"   • Articles received: {stats['articles_delivered']}")
        if stats['articles_delivered'] > 0:
            print(f"   • Average match score: {stats['average_similarity']:.2%}")
    
    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80)
    
    print("\n  Summary:")
    print(f"   • Users created: {len(users)}")
    print(f"   • Keywords configured: {sum(len(u['keywords']) for u in users)}")
    print(f"   • Articles processed: {len(test_articles)}")
    
    total_deliveries = sum(r['users_delivered'] for r in results.values())
    print(f"   • Total article deliveries: {total_deliveries}")
    
    print("\nVerification:")
    all_correct = True
    for article in test_articles:
        article_id = article['id']
        expected_users = set(article['should_match'])
        
        delivered_usernames = set()
        delivery_summary = keyword_matcher.dispatch_article_to_users(article["id"])
        for user_id in delivery_summary.keys():
            username = next((k for k, v in user_ids.items() if v == user_id), None)
            if username:
                delivered_usernames.add(username)
        
        if delivered_usernames == expected_users:
            print(f"    {article['title'][:40]}... - Correct!")
        else:
            print(f"    {article['title'][:40]}... - Mismatch!")
            print(f"      Expected: {expected_users}")
            print(f"      Got: {delivered_usernames}")
            all_correct = False
    
    if all_correct:
        print("\n All articles dispatched correctly!")
    else:
        print("\n /!\  Some mismatches detected (might be due to embedding variations)")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    try:
        demo_workflow()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted")
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        import traceback
        traceback.print_exc()
