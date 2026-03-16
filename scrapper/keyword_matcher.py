"""
Keyword Matcher - Matches articles with user keywords using embedding similarity.

This module handles:
1. Computing embeddings for user keywords
2. Finding matching articles for keywords
3. Distributing articles to users
"""

import logging
from typing import Dict, List, Optional, Any
import numpy as np

from database import DatabaseManager
from embeddings import EmbeddingManager

logger = logging.getLogger(__name__)


class KeywordMatcher:
    """Matches articles with user keywords using embeddings."""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        embedding_manager: EmbeddingManager,
        similarity_threshold: float = 0.7
    ):
        """
        Initialize the keyword matcher.
        
        Args:
            db_manager: Database manager instance
            embedding_manager: Embedding manager instance
            similarity_threshold: Minimum similarity score (0-1) for matches
        """
        self.db_manager = db_manager
        self.embedding_manager = embedding_manager
        self.similarity_threshold = similarity_threshold

    def setup_user_keywords(self, user_id: int, keywords: List[str]) -> Dict[int, str]:
        """
        Setup keywords for a user and compute their embeddings.
        
        Args:
            user_id: User ID
            keywords: List of keywords to add
            
        Returns:
            Dictionary mapping keyword_id to keyword text
        """
        keyword_map = {}
        
        for keyword in keywords:
            try:
                keyword_id = self.db_manager.add_user_keyword(user_id, keyword)
                
                embedding = self.embedding_manager.embed_text(keyword)
                
                self.db_manager.store_keyword_embedding(
                    keyword_id=keyword_id,
                    user_id=user_id,
                    keyword=keyword,
                    embedding=embedding
                )
                
                keyword_map[keyword_id] = keyword
                logger.info(f"✓ Keyword '{keyword}' added for user {user_id} (ID: {keyword_id})")
                
            except Exception as e:
                logger.error(f"✗ Failed to add keyword '{keyword}': {e}")
        
        return keyword_map

    def match_article_with_keywords(self, article_id: str) -> List[Dict[str, Any]]:
        """
        Find all users who should receive an article based on keyword matching.
        
        Args:
            article_id: Article ID to match
            
        Returns:
            List of matching results with user info and similarity scores
        """
        try:
            # Get matching keywords for the article
            matches = self.db_manager.find_matching_keywords(
                article_id=article_id,
                similarity_threshold=self.similarity_threshold
            )
            
            if not matches:
                logger.debug(f"No keyword matches found for article {article_id}")
                return []
            
            logger.info(f"Found {len(matches)} keyword matches for article {article_id}")
            return matches
            
        except Exception as e:
            logger.error(f"Error matching article {article_id}: {e}")
            return []

    def dispatch_article_to_users(self, article_id: str) -> Dict[int, List[str]]:
        """
        Distribute an article to all matching users.
        
        This is the main workflow:
        1. Find all keywords matching the article
        2. Group matches by user (avoiding duplicate users)
        3. Record delivery with best matching keyword per user
        
        Args:
            article_id: Article ID to distribute
            
        Returns:
            Dictionary mapping user_id to list of matched keywords
        """
        matches = self.match_article_with_keywords(article_id)
        
        if not matches:
            return {}
        
        user_matches: Dict[int, Dict[str, Any]] = {}
        
        for match in matches:
            user_id = match["user_id"]
            
            if user_id not in user_matches or match["similarity_score"] > user_matches[user_id]["similarity_score"]:
                user_matches[user_id] = match
        
        delivery_summary = {}
        
        for user_id, match in user_matches.items():
            try:
                self.db_manager.record_article_delivery(
                    user_id=user_id,
                    article_id=article_id,
                    keyword_id=match["keyword_id"],
                    similarity_score=match["similarity_score"]
                )
                
                if user_id not in delivery_summary:
                    delivery_summary[user_id] = []
                
                delivery_summary[user_id].append(match["keyword"])
                
                logger.info(
                    f"✓ Article {article_id} delivered to user {user_id} ({match['username']}) "
                    f"via keyword '{match['keyword']}' (similarity: {match['similarity_score']:.3f})"
                )
                
            except Exception as e:
                logger.error(f"✗ Failed to deliver article {article_id} to user {user_id}: {e}")
        
        return delivery_summary

    def batch_dispatch_articles(self, article_ids: List[str]) -> Dict[str, Dict[int, List[str]]]:
        """
        Dispatch multiple articles to users.
        
        Args:
            article_ids: List of article IDs
            
        Returns:
            Dictionary mapping article_id to delivery summaries
        """
        results = {}
        
        for article_id in article_ids:
            results[article_id] = self.dispatch_article_to_users(article_id)
        
        return results

    def get_user_personalized_feed(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get personalized feed for a user (articles matched to their keywords).
        
        Args:
            user_id: User ID
            limit: Maximum articles to return
            
        Returns:
            List of articles with match information
        """
        return self.db_manager.get_user_articles(user_id, limit)

    def print_matching_summary(self, article_id: str) -> None:
        """Print a summary of keyword matches for an article."""
        matches = self.match_article_with_keywords(article_id)
        
        if not matches:
            print(f"No matches found for article {article_id}")
            return
        
        user_matches = {}
        for match in matches:
            user_id = match["user_id"]
            if user_id not in user_matches:
                user_matches[user_id] = {
                    "username": match["username"],
                    "keywords": []
                }
            user_matches[user_id]["keywords"].append({
                "keyword": match["keyword"],
                "score": match["similarity_score"]
            })
        
        print(f"\nKeyword Matches for Article {article_id}:")
        print("=" * 60)
        
        for user_id, user_info in user_matches.items():
            print(f"\n{user_info['username']} (User #{user_id}):")
            for kw_info in user_info["keywords"]:
                score_pct = kw_info["score"] * 100
                print(f"   - '{kw_info['keyword']}' → {score_pct:.1f}%")
