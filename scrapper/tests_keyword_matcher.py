"""
Tests for the User Keywords Filtering System

Run with: pytest tests_keyword_matcher.py -v
"""

import os
import sys
from typing import Optional
import numpy as np

# Mock classes for testing without database
class MockDatabaseManager:
    """Mock database manager for testing."""
    
    def __init__(self):
        self.users = {}
        self.keywords = {}
        self.keyword_embeddings = {}
        self.deliveries = {}
        self.articles = {}
        self.articles_embeddings = {}
        self.next_user_id = 1
        self.next_keyword_id = 1
    
    def add_user(self, username: str, email: Optional[str] = None) -> int:
        user_id = self.next_user_id
        self.users[user_id] = {"username": username, "email": email}
        self.next_user_id += 1
        return user_id
    
    def add_user_keyword(self, user_id: int, keyword: str) -> int:
        keyword_id = self.next_keyword_id
        self.keywords[keyword_id] = {"user_id": user_id, "keyword": keyword}
        self.next_keyword_id += 1
        return keyword_id
    
    def store_keyword_embedding(self, keyword_id: int, user_id: int, keyword: str, 
                               embedding: np.ndarray, embedding_model: str = "test"):
        self.keyword_embeddings[keyword_id] = {
            "user_id": user_id,
            "keyword": keyword,
            "embedding": embedding
        }
    
    def find_matching_keywords(self, article_id: str, similarity_threshold: float = 0.7):
        """Calculate similarity between article and keywords."""
        if article_id not in self.articles_embeddings:
            return []
        
        article_emb = self.articles_embeddings[article_id]
        matches = []
        
        for kw_id, kw_data in self.keyword_embeddings.items():
            # Cosine similarity
            similarity = self._cosine_similarity(article_emb, kw_data["embedding"])
            
            if similarity >= similarity_threshold:
                keyword = self.keywords[kw_id]
                matches.append({
                    "user_id": keyword["user_id"],
                    "username": self.users[keyword["user_id"]]["username"],
                    "email": self.users[keyword["user_id"]]["email"],
                    "keyword_id": kw_id,
                    "keyword": keyword["keyword"],
                    "similarity_score": similarity
                })
        
        return sorted(matches, key=lambda x: x["similarity_score"], reverse=True)
    
    def record_article_delivery(self, user_id: int, article_id: str, 
                               keyword_id: int, similarity_score: float):
        key = (user_id, article_id)
        self.deliveries[key] = {
            "keyword_id": keyword_id,
            "similarity_score": similarity_score
        }
    
    def get_user_articles(self, user_id: int, limit: int = 50):
        articles = []
        for (u_id, article_id), delivery in self.deliveries.items():
            if u_id == user_id:
                kw_id = delivery["keyword_id"]
                keyword = self.keywords[kw_id]["keyword"]
                articles.append({
                    "article_id": article_id,
                    "keyword": keyword,
                    "similarity_score": delivery["similarity_score"]
                })
        return articles[:limit]
    
    def get_user_stats(self, user_id: int):
        if user_id not in self.users:
            return {}
        
        keywords_count = sum(1 for kw in self.keywords.values() if kw["user_id"] == user_id)
        articles = self.get_user_articles(user_id, limit=10000)
        avg_score = np.mean([a["similarity_score"] for a in articles]) if articles else 0.0
        
        return {
            "user_id": user_id,
            "username": self.users[user_id]["username"],
            "keywords_count": keywords_count,
            "articles_delivered": len(articles),
            "average_similarity": round(float(avg_score), 3)
        }
    
    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))


def create_test_embedding(text: str) -> np.ndarray:
    """Create a simple deterministic embedding for testing."""
    # Use text hash to create reproducible random embedding
    np.random.seed(hash(text) % (2**32))
    return np.random.randn(10)  # 10-dimensional for simplicity


def test_user_creation():
    """Test: Create users."""
    db = MockDatabaseManager()
    
    user1_id = db.add_user("alice", "alice@example.com")
    user2_id = db.add_user("bob", "bob@example.com")
    
    assert user1_id == 1
    assert user2_id == 2
    assert db.users[user1_id]["username"] == "alice"
    print("✅ test_user_creation passed")


def test_keyword_setup():
    """Test: Add keywords to user."""
    db = MockDatabaseManager()
    
    user_id = db.add_user("alice")
    
    kw1_id = db.add_user_keyword(user_id, "machine learning")
    kw2_id = db.add_user_keyword(user_id, "deep learning")
    
    assert kw1_id == 1
    assert kw2_id == 2
    assert db.keywords[kw1_id]["keyword"] == "machine learning"
    print("✅ test_keyword_setup passed")


def test_keyword_embeddings():
    """Test: Store keyword embeddings."""
    db = MockDatabaseManager()
    
    user_id = db.add_user("alice")
    kw_id = db.add_user_keyword(user_id, "machine learning")
    
    embedding = create_test_embedding("machine learning")
    db.store_keyword_embedding(kw_id, user_id, "machine learning", embedding)
    
    assert kw_id in db.keyword_embeddings
    assert db.keyword_embeddings[kw_id]["keyword"] == "machine learning"
    print("✅ test_keyword_embeddings passed")


def test_similarity_matching():
    """Test: Matching articles with keywords."""
    db = MockDatabaseManager()
    
    # Create user with keyword
    user_id = db.add_user("alice")
    kw_id = db.add_user_keyword(user_id, "machine learning")
    
    # Create keyword embedding
    kw_embedding = create_test_embedding("machine learning")
    db.store_keyword_embedding(kw_id, user_id, "machine learning", kw_embedding)
    
    # Simulate article with similar embedding
    article_id = "article_001"
    article_embedding = kw_embedding + np.random.randn(10) * 0.1  # Similar but not identical
    db.articles_embeddings[article_id] = article_embedding
    
    # Find matches
    matches = db.find_matching_keywords(article_id, similarity_threshold=0.7)
    
    # Should find a match since embeddings are similar
    assert len(matches) > 0
    assert matches[0]["keyword"] == "machine learning"
    assert matches[0]["similarity_score"] > 0.7
    print("✅ test_similarity_matching passed")


def test_no_match_for_dissimilar():
    """Test: No match for dissimilar articles."""
    db = MockDatabaseManager()
    
    # Create user with keyword
    user_id = db.add_user("alice")
    kw_id = db.add_user_keyword(user_id, "machine learning")
    
    # Create keyword embedding
    kw_embedding = create_test_embedding("machine learning")
    db.store_keyword_embedding(kw_id, user_id, "machine learning", kw_embedding)
    
    # Simulate article with very different embedding
    article_id = "article_001"
    article_embedding = np.random.randn(10) * 5  # Very different
    db.articles_embeddings[article_id] = article_embedding
    
    # Find matches
    matches = db.find_matching_keywords(article_id, similarity_threshold=0.7)
    
    # Should not find a match
    assert len(matches) == 0
    print("✅ test_no_match_for_dissimilar passed")


def test_article_delivery():
    """Test: Record article delivery."""
    db = MockDatabaseManager()
    
    user_id = db.add_user("alice")
    kw_id = db.add_user_keyword(user_id, "machine learning")
    
    article_id = "article_001"
    similarity_score = 0.85
    
    db.record_article_delivery(user_id, article_id, kw_id, similarity_score)
    
    user_articles = db.get_user_articles(user_id)
    assert len(user_articles) == 1
    assert user_articles[0]["article_id"] == article_id
    print("✅ test_article_delivery passed")


def test_user_stats():
    """Test: Calculate user statistics."""
    db = MockDatabaseManager()
    
    user_id = db.add_user("alice")
    kw1_id = db.add_user_keyword(user_id, "machine learning")
    kw2_id = db.add_user_keyword(user_id, "deep learning")
    
    # Record deliveries
    db.record_article_delivery(user_id, "article_001", kw1_id, 0.85)
    db.record_article_delivery(user_id, "article_002", kw2_id, 0.75)
    
    stats = db.get_user_stats(user_id)
    
    assert stats["username"] == "alice"
    assert stats["keywords_count"] == 2
    assert stats["articles_delivered"] == 2
    print("✅ test_user_stats passed")


def test_multiple_users():
    """Test: Multiple users with different keywords."""
    db = MockDatabaseManager()
    
    # User 1: AI keywords
    user1_id = db.add_user("alice")
    kw1_1 = db.add_user_keyword(user1_id, "machine learning")
    
    # User 2: Web keywords
    user2_id = db.add_user("bob")
    kw2_1 = db.add_user_keyword(user2_id, "React")
    
    # Store embeddings
    db.store_keyword_embedding(kw1_1, user1_id, "machine learning", 
                              create_test_embedding("machine learning"))
    db.store_keyword_embedding(kw2_1, user2_id, "React",
                              create_test_embedding("React"))
    
    # Article about ML should match only alice
    article_id = "article_001"
    db.articles_embeddings[article_id] = create_test_embedding("machine learning")
    
    matches = db.find_matching_keywords(article_id, similarity_threshold=0.7)
    
    assert len(matches) > 0
    assert all(m["user_id"] == user1_id for m in matches)
    print("✅ test_multiple_users passed")


def run_all_tests():
    """Run all tests."""
    tests = [
        test_user_creation,
        test_keyword_setup,
        test_keyword_embeddings,
        test_similarity_matching,
        test_no_match_for_dissimilar,
        test_article_delivery,
        test_user_stats,
        test_multiple_users,
    ]
    
    print("\n" + "="*60)
    print("🧪 Running User Keywords Filtering System Tests")
    print("="*60 + "\n")
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} error: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
